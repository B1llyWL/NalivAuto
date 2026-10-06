from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def yes_no_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅",callback_data="answer_yes"),
        InlineKeyboardButton("❌",callback_data="answer_no")
    )
    return kb

def done_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅Готово",callback_data="done")
    )
    return kb

def role_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
      InlineKeyboardButton("👤 Водитель", callback_data="who_driver"),
    )
    return kb