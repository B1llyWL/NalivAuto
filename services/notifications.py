import sys
from config import LOGIST_IDS as LOGIST_CHAT_IDS
from database import get_session
from models import DriverDoc

def notify_logists(bot, text):
    for chat_id in LOGIST_CHAT_IDS:
        try:
            bot.send_message(chat_id, text)
        except Exception as e:
            print(f"[NOTIFY] Ошибка: {e}", file=sys.stderr, flush=True)

def send_reason_to_logists(bot, user_id, group_id, reason_text):
    notify_logists(bot, f"📝 Водитель {user_id} в группе {group_id} указал причину:\n{reason_text}")

def send_docs_to_logists(bot, user_id, group_id):
    session = get_session()
    try:
        docs = session.query(DriverDoc).filter_by(telegram_id=user_id, group_id=group_id).all()
        if not docs:
            docs = session.query(DriverDoc).filter_by(telegram_id=user_id).all()
        if not docs:
            notify_logists(bot, f"⚠️ У водителя {user_id} нет сохранённых документов.")
            return
        delivered = 0
        failed = 0
        for chat_id in LOGIST_CHAT_IDS:
            try:
                first = docs[0]
                caption = f"📦 Документы от водителя {user_id}\nГруппа: {group_id}\nФайлов: {len(docs)}"
                if first.file_type == "photo":
                    bot.send_photo(chat_id, first.file_id, caption=caption)
                else:
                    bot.send_document(chat_id, first.file_id, caption=caption)
                for doc in docs[1:]:
                    if doc.file_type == "photo":
                        bot.send_photo(chat_id, doc.file_id)
                    else:
                        bot.send_document(chat_id, doc.file_id)
                delivered += 1
            except Exception as e:
                failed += 1
                print(f"[NOTIFY] Ошибка отправки документов в {chat_id}: {e}", file=sys.stderr, flush=True)
        if delivered > 0:
            for doc in docs:
                session.delete(doc)
            session.commit()
            if failed:
                notify_logists(bot, f"⚠️ Документы водителя {user_id} доставлены не всем логистам (ошибок: {failed}).")
        else:
            notify_logists(bot, f"⛔ Документы водителя {user_id} НЕ доставлены никому - файлы оставлены в БД.")
    except Exception as e:
        print(f"[NOTIFY] Ошибка send_docs: {e}", file=sys.stderr, flush=True)
        session.rollback()
    finally:
        session.close()