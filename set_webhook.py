import telebot
from config import BOT_TOKEN, WEBHOOK_URL

bot = telebot.TeleBot(BOT_TOKEN)

bot.remove_webhook()
bot.set_webhook(
    url=WEBHOOK_URL,
    allowed_updates=["message", "callback_query", "my_chat_member", "chat_member"]
)

print(f"✅ Webhook установлен: {WEBHOOK_URL}")
info = bot.get_webhook_info()
print(f"📌 Текущий webhook: {info.url}")