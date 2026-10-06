import sys
from telebot import TeleBot
from telebot.types import ChatMemberUpdated
from database import get_session
from models import Group
from services.helpers import get_or_create_user
from keyboards import role_keyboard

def register(bot: TeleBot):
    """Регистрируем обработчики групп."""

    @bot.my_chat_member_handler()
    def handle_my_chat_member(update: ChatMemberUpdated):
        chat = update.chat
        if chat.type not in ("group", "supergroup"):
            return

        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status

        bot_added = old_status in ("left", "kicked") and \
            new_status in ("member", "administrator", "restricted")
        bot_removed = old_status in ("member", "administrator", "restricted") and \
            new_status in ("left", "kicked")

        session = get_session()
        try:
            existing = session.query(Group).filter_by(chat_id=chat.id).first()

            if bot_added:
                if existing:
                    existing.is_active = True
                    existing.group_name = chat.title
                else:
                    by_name = session.query(Group).filter_by(group_name=chat.title).first()
                    if by_name:
                        by_name.chat_id = chat.id
                        by_name.is_active = True
                    else:
                        session.add(Group(chat_id=chat.id, group_name=chat.title))
                session.commit()

                bot.send_message(chat.id, f"Здравствуйте! Бот подключен к группе «{chat.title}».")
                bot.send_message(
                    chat.id,
                    "👋 Кто вы? Нажмите кнопку, чтобы бот запомнил вашу роль.",
                    reply_markup=role_keyboard()
                )

            elif bot_removed:
                if existing:
                    existing.is_active = False
                    session.commit()
        except Exception as e:
            print(f"[GROUPS] Ошибка my_chat_member: {e}", file=sys.stderr, flush=True)
            session.rollback()
        finally:
            session.close()

    @bot.callback_query_handler(
        func=lambda call: call.data == "who_driver")
    def handle_who_driver(call):
        user_id = call.from_user.id
        group_id = call.message.chat.id
        get_or_create_user(user_id, call.from_user.username)
        name = call.from_user.first_name or "Пользователь"
        session = get_session()
        try:
            group = session.query(Group).filter_by(chat_id=group_id).first()
            if group:
                group.driver_id = user_id
                session.commit()
            text = f"✅ {name} назначен <b>водителем</b> этой группы. Бот будет отмечать его."
        except Exception as e:
            print(f"[GROUPS] Ошибка who: {e}", file=sys.stderr, flush=True)
            session.rollback()
            text = "⚠️ Произошла ошибка, попробуйте ещё раз."
        finally:
            session.close()

        bot.answer_callback_query(call.id)
        try:
            bot.send_message(group_id, text, parse_mode="HTML")
        except Exception:
            pass