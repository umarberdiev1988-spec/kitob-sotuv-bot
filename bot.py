import os
import telebot
from telebot import types

# BotFather'дан олган TOKEN'ингизни Render'да BOT_TOKEN орқали ёки шу ерга ёзасиз
TOKEN = os.environ.get('BOT_TOKEN', 'TOKENINGIZNI_SHU_YERGA_YOZING')
bot = telebot.TeleBot(TOKEN)

# Китоб ва бонус Google Sheets ҳаволалари
BOOK_LINK = "https://docs.google.com/document/d/1t-nOP2ymUKZsAWFz9OV9KPSvMO6zol7Js9YyqoOiD40/edit?usp=drivesdk"
BONUS_SHEET_LINK = "https://docs.google.com/spreadsheets/d/12t7vV5iAvazFr2n4-rg9wIOUMFkXEp8sVaVXJEw2VVw/edit?usp=drivesdk"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name or "дўст"

    welcome_text = (
        f"Ассалому алайкум, {user_name}!\n\n"
        f"📖 *«Қоғозбозликдан рақамли тизимларга»* китоби ва унинг бонусли электрон жадвалини сотиб олганингиз учун раҳмат!\n\n"
        f"Қуйидаги тугмалар орқали китоб ва бонус файлни очишингиз ва Google Drive'га нусха қилиб ишлашингиз мумкин:"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_book = types.InlineKeyboardButton("📖 Китобни ўқиш (Google Docs)", url=BOOK_LINK)
    btn_bonus = types.InlineKeyboardButton("📊 Бонус Жадвал (Google Sheets)", url=BONUS_SHEET_LINK)

    markup.add(btn_book, btn_bonus)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Бот фаолият кўрсатмоқда. Китобни олиш учун /start буйруғини босинг.")

if __name__ == '__main__':
    print("Бот ишга тушди...")
    bot.infinity_polling()
