import sys
from datetime import datetime, timedelta
from config import LOGIST_IDS
from database import get_session
from models import DriverDoc, DriverReason, ScheduledTask, Group
from services.helpers import get_or_create_user, set_user_state, get_user_state
from services.notifications import notify_logists, send_docs_to_logists, send_reason_to_logists
from parsers import parse_delay_minutes
from keyboards import yes_no_keyboard, done_keyboard
from constants import (
    MSG_LOAD_QUESTION, MSG_DOC_CHECK_QUESTION, MSG_DOC_INVALID_WARNING,
    MSG_DOCS_SENT, MSG_WAITING_FILES, MSG_WAITING_REASON, MSG_WAITING_DELAY
)


def driver_mention(driver_id):
    if driver_id:
        return f'<a href="tg://user?id={driver_id}">Водитель</a>, '
    return ""


def register(bot):
    @bot.message_handler(commands=["ask"])
    def cmd_ask(message):
        if message.from_user.id not in LOGIST_IDS:
            bot.reply_to(message, "⛔ Команда доступна только логистам.")
            return
        user_id = message.from_user.id
        group_id = message.chat.id
        get_or_create_user(user_id, message.from_user.username)

        session = get_session()
        try:
            group = session.query(Group).filter_by(chat_id=group_id).first()
            driver_id = group.driver_id if group else None
        finally:
            session.close()

        mention = driver_mention(driver_id)
        bot.send_message(
            group_id,
            mention + MSG_LOAD_QUESTION,
            reply_markup=yes_no_keyboard(),
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data in ("answer_yes", "answer_no"))
    def cb_answer(call):
        user_id = call.from_user.id
        group_id = call.message.chat.id
        get_or_create_user(user_id, call.from_user.username)
        current_state = get_user_state(user_id)

        try:
            bot.edit_message_reply_markup(group_id, call.message.message_id)
        except Exception:
            pass

        session = get_session()
        try:
            group = session.query(Group).filter_by(chat_id=group_id).first()
            driver_id = group.driver_id if group else None
        finally:
            session.close()

        mention = driver_mention(driver_id)

        # ПРОВЕРКА СМР ПЕРЕД ОТПРАВКОЙ 
        if current_state == "waiting_doc_check":
            if call.data == "answer_yes":
                set_user_state(user_id, "idle")
                send_docs_to_logists(bot, user_id, group_id)
                bot.send_message(group_id, MSG_DOCS_SENT, parse_mode="HTML")
                notify_logists(bot, f"✅ Водитель {user_id} завершил отправку документов.")
            else:
                # Нет — просим переделать
                set_user_state(user_id, "waiting_files")
                bot.send_message(group_id, mention + MSG_DOC_INVALID_WARNING, parse_mode="HTML")
                bot.send_message(
                    group_id,
                    MSG_WAITING_FILES,
                    reply_markup=done_keyboard(),
                    parse_mode="HTML"
                )
                notify_logists(bot, f"🟡 Водитель {user_id} указал, что документы не готовы.")
            bot.answer_callback_query(call.id)
            return

        # ПЕРВИЧНЫЙ ОТВЕТ НА ВОПРОС "ЗАГРУЗИЛИСЬ?"
        if call.data == "answer_yes":
            set_user_state(user_id, "waiting_files")
            bot.send_message(
                group_id,
                mention + MSG_WAITING_FILES,
                reply_markup=done_keyboard(),
                parse_mode="HTML"
            )
            notify_logists(bot, f"🟢 Водитель {user_id} ответил «Да» — ждём документы.")
        else:
            set_user_state(user_id, "waiting_reason")
            bot.send_message(group_id, mention + MSG_WAITING_REASON, parse_mode="HTML")
            notify_logists(bot, f"🟡 Водитель {user_id} ответил «Нет» — ждём причину.")

        bot.answer_callback_query(call.id)

    @bot.message_handler(
        content_types=["text"],
        func=lambda m: get_user_state(m.from_user.id) == "waiting_reason"
    )
    def handle_reason(message):
        user_id = message.from_user.id
        group_id = message.chat.id
        reason_text = message.text.strip()
        session = get_session()
        try:
            reason = DriverReason(
                telegram_id=user_id,
                group_id=group_id,
                reason_text=reason_text
            )
            session.add(reason)
            session.commit()
        finally:
            session.close()
        send_reason_to_logists(bot, user_id, group_id, reason_text)
        set_user_state(user_id, "waiting_delay")
        bot.send_message(group_id, MSG_WAITING_DELAY)

    @bot.message_handler(
        content_types=["text"],
        func=lambda m: get_user_state(m.from_user.id) == "waiting_delay"
    )
    def handle_delay(message):
        user_id = message.from_user.id
        group_id = message.chat.id
        text = message.text.strip()
        result = parse_delay_minutes(text)
        if result is None:
            bot.reply_to(
                message,
                "Не понял время. Примеры:\n"
                "• 20\n"
                "• 1 час 20 минут\n"
                "• завтра\n"
                "• завтра в 14:30"
            )
            return
        rtype, rval = result
        set_user_state(user_id, "idle")
        if rtype == "minutes":
            remind_at = datetime.utcnow() + timedelta(minutes=rval)
            answer = f"Хорошо, напомню через {rval} мин."
        else:
            remind_at = rval
            msk = rval + timedelta(hours=3)
            answer = f"Хорошо, напомню {msk.strftime('%d.%m в %H:%M')} по МСК."
        session = get_session()
        try:
            task = ScheduledTask(
                task_type="remind_driver",
                target_id=user_id,
                send_at=remind_at,
                text=str(group_id)
            )
            session.add(task)
            session.commit()
        finally:
            session.close()
        bot.send_message(group_id, answer)
        notify_logists(bot, f"⏰ Водитель {user_id} попросил напомнить: {text}")

    @bot.message_handler(
        content_types=["photo", "document"],
        func=lambda m: get_user_state(m.from_user.id) == "waiting_files"
    )
    def handle_docs(message):
        user_id = message.from_user.id
        group_id = message.chat.id
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        else:
            file_id = message.document.file_id
            file_type = "document"
        session = get_session()
        try:
            doc = DriverDoc(
                telegram_id=user_id,
                group_id=group_id,
                file_id=file_id,
                file_type=file_type
            )
            session.add(doc)
            session.commit()
        except Exception as e:
            print(f"[DRIVER] Ошибка сохранения: {e}", file=sys.stderr, flush=True)
            session.rollback()
        finally:
            session.close()
        bot.reply_to(message, "📥 Принято.")

    @bot.callback_query_handler(func=lambda call: call.data == "done")
    def cb_done(call):
        user_id = call.from_user.id
        group_id = call.message.chat.id

        # ПЕРЕД ОТПРАВКОЙ СПРАШИВАЕМ ПРО ДАТУ/ПОДПИСЬ 
        set_user_state(user_id, "waiting_doc_check")

        try:
            bot.edit_message_reply_markup(group_id, call.message.message_id)
        except Exception:
            pass

        bot.send_message(
            group_id,
            MSG_DOC_CHECK_QUESTION,
            reply_markup=yes_no_keyboard(),
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)