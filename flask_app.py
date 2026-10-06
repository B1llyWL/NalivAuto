import sys, time, telebot, traceback
from flask import Flask, request
from config import WEBHOOK_PATH
from database import init_db, get_session
from models import Group
from bot import bot
from services.scheduler import process_scheduled_tasks, process_assignments

init_db()
app = Flask(__name__)

_LAST_SCHED_RUN = {"ts": 0.0}
SCHED_MIN_INTERVAL = 60


@app.route("/")
def index():
    return "✅ Бот работает!"


def ensure_group_in_db(chat):
    """Самовосстановление: сообщение из группы, которой нет в БД → регистрируем."""
    if chat.type not in ("group", "supergroup"):
        return
    session = get_session()
    try:
        if not session.query(Group).filter_by(chat_id=chat.id).first():
            session.add(Group(chat_id=chat.id, group_name=chat.title))
            session.commit()
            print(f"[GROUPS] Группа «{chat.title}» автоматически добавлена в БД", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[GROUPS] Ошибка ensure_group: {e}", file=sys.stderr, flush=True)
        session.rollback()
    finally:
        session.close()


def run_scheduler_safe(source):
    try:
        process_scheduled_tasks(bot)
    except Exception as e:
        print(f"[SCHED] Ошибка tasks ({source}): {e}", file=sys.stderr, flush=True)
    try:
        process_assignments(bot)
    except Exception as e:
        print(f"[SCHED] Ошибка assignments ({source}): {e}", file=sys.stderr, flush=True)


def maybe_run_scheduler():
    """Страховка: при любой активности бота прогоняем планировщик, не чаще раза в минуту."""
    now = time.time()
    if now - _LAST_SCHED_RUN["ts"] < SCHED_MIN_INTERVAL:
        return
    _LAST_SCHED_RUN["ts"] = now
    run_scheduler_safe("webhook")


@app.route("/check-scheduled")
def check_scheduled():
    print("[SCHED] /check-scheduled вызван", file=sys.stderr, flush=True)
    run_scheduler_safe("cron")
    return "OK", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    try:
        update = telebot.types.Update.de_json(json_str)
        if update.message and update.message.chat:
            ensure_group_in_db(update.message.chat)
        bot.process_new_updates([update])
        maybe_run_scheduler()
    except Exception:
        print("[WEBHOOK] Ошибка обработки апдейта:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
    return "OK", 200