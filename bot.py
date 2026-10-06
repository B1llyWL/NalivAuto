import telebot
from config import BOT_TOKEN
from database import init_db
from handlers import start, driver, admin, groups

init_db()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

start.register(bot)
driver.register(bot)
admin.register(bot)
groups.register(bot)
print(f"Зарегистрировано хендлеров: {len(bot.message_handlers)}", flush=True)