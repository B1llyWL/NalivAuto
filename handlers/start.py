import sys
from telebot import types
from database import get_session
from models import ScheduledTask
from services.helpers import get_or_create_user, is_logist
from keyboards import role_keyboard

def register(bot):
    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        if message.chat.type == "private":
            bot.send_message(
                message.chat.id,
                "👋 Здравствуйте! Я работаю в группах.\n"
                "Добавьте меня в нужный чат, и я буду задавать вопросы водителям.\n\n"
                "Подробнее: /info"
            )
            return
        get_or_create_user(message.from_user.id, message.from_user.username)
        bot.send_message(message.chat.id, "👋 Бот активирован. Ждите вопросы от логиста.")

    @bot.message_handler(commands=["info"])
    def cmd_info(message):
        text = (
            "ℹ️ <b>О боте</b>\n\n"
            "Бот помогает логистам отслеживать загрузку водителей:\n"
            "• задаёт вопросы в группах\n"
            "• принимает фото документов\n"
            "• делает рассылки и запланированные рейсы\n\n"
            "⏰ <b>Как работает напоминание</b>\n"
            "Рассылки и рейсы отправляются автоматически через внешний сервис "
            "<b>cron-job.org</b>. Он каждые 5 минут стучится на сервер, "
            "чтобы бот проверил, нет ли просроченных задач.\n\n"
            "📅 <b>Важно: активация раз в месяц</b>\n"
            "Сервер работает на бесплатном тарифе PythonAnywhere, "
            "поэтому <b>раз в месяц</b> нужно:\n"
            "1. Зайти в консоль PythonAnywhere\n"
            "2. Нажать зелёную кнопку <b>Reload</b> на вкладке Web\n"
            "Иначе сервер «заснёт» и бот перестанет отвечать.\n\n"
            "📋 <b>Команды для логистов:</b> /help\n"
            "👥 <b>Список групп:</b> /groups"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(commands=["who"])
    def cmd_who(message):
        if message.chat.type == "private":
            bot.reply_to(message, "⚠️ Эта команда работает только в группах.")
            return
        bot.send_message(
            message.chat.id,
            "👋 Кто вы? Нажмите кнопку, чтобы бот запомнил вашу роль.",
            reply_markup=role_keyboard()
        )

    @bot.message_handler(commands=["tasks"])
    def cmd_tasks(message):
        if not is_logist(message.from_user.id):
            return
        session = get_session()
        try:
            tasks = session.query(ScheduledTask).filter_by(is_sent=False).all()
            if not tasks:
                bot.reply_to(message, "Нет отложенных задач.")
                return
            text = "⏰ Отложенные задачи:\n\n"
            for t in tasks:
                kind = "ежедневно" if t.daily else "единоразово"
                text += f"#{t.id} [{t.task_type}, {kind}] {t.send_at.strftime('%d.%m %H:%M')}\n"
                if t.text:
                    text += f" Текст: {t.text[:50]}\n"
            text += "\nУдалить: /deltask НОМЕР"
            bot.reply_to(message, text)
        finally:
            session.close()