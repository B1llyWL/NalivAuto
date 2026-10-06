import sys, os

# Путь к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telebot import TeleBot
from config import BOT_TOKEN
from services.scheduler import process_scheduled_tasks, process_assignments


def run_cron_task():
    """Один проход планировщика: просроченные задачи и рейсы.
    Ежедневные сдвигаются на +1 день, единоразовые помечаются отправленными."""
    bot = TeleBot(BOT_TOKEN)
    process_scheduled_tasks(bot)
    process_assignments(bot)


if __name__ == "__main__":
    run_cron_task()