import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

BOOK_LINK = "https://docs.google.com/document/d/1t-nOP2ymUKZsAWFz9OV9KPSvMO6zol7Js9YyqoOiD40/edit?usp=drivesdk"
BONUS_SHEET_LINK = "https://docs.google.com/spreadsheets/d/12t7vV5iAvazFr2n4-rg9wIOUMFkXEp8sVaVXJEw2VVw/edit?usp=drivesdk"

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name or "дўст"

    welcome_text = (
        f"Ассалому алайкум, {user_name}!\n\n"
        f"📖 *«Қоғозбозликдан рақамли тизимларга»* китоби ва бонус жадвалини танлаганингиз учун раҳмат!\n\n"
        f"Қуйидаги тугмалар орқали китоб ва бонус файлни очишингиз ва Google Drive'га нусха қилиб ишлашингиз мумкин:"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_book = types.InlineKeyboardButton("📖 Китобни ўқиш (Google Docs)", url=BOOK_LINK)
    btn_bonus = types.InlineKeyboardButton("📊 Бонус Жадвал (Google Sheets)", url=BONUS_SHEET_LINK)

    markup.add(btn_book, btn_bonus)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Бот ишламоқда. Китоб ва бонус жадвални олиш учун /start буйруғини босинг.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    print("Бот ва веб-сервер ишга тушди...")
    bot.infinity_polling(none_stop=True)
