import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
CARD_NUMBER = os.environ.get('CARD_NUMBER', '9860 0101 1982 2228')
CARD_OWNER = os.environ.get('CARD_OWNER', 'Umar Berdiev')
BOOK_PRICE = os.environ.get('BOOK_PRICE', '29 000 сўм')

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

def send_book_and_bonus(chat_id):
    text = (
        "🎉 *Тўловингиз тасдиқланди!*\n\n"
        "📖 *«Қоғозбозликдан рақамли тизимларга»* амалий қўлланмаси ва бонус жадвалингиз тайёр.\n"
        "Қуйидаги тугмалар орқали очиб, ўзингизнинг Google Drive'ингизга нусха олиб ишлатишингиз мумкин:"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_book = types.InlineKeyboardButton("📖 Китобни ўқиш (Google Docs)", url=BOOK_LINK)
    btn_bonus = types.InlineKeyboardButton("📊 Бонус Жадвал (Google Sheets)", url=BONUS_SHEET_LINK)
    markup.add(btn_book, btn_bonus)
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name or "дўст"

    welcome_text = (
        f"Ассалому алайкум, {user_name}!\n\n"
        f"📖 *«Қоғозбозликдан рақамли тизимларга»* амалий қўлланмаси + бонус *«Молиявий Назорат Жадвали»* (Google Sheets).\n\n"
        f"💰 *Нархи:* {BOOK_PRICE}\n"
        f"💳 *Тўлов учун карта:* `{CARD_NUMBER}`\n"
        f"👤 *Карта эгаси:* {CARD_OWNER}\n\n"
        f"Тўловни амалга оширгач, *чек расмини (скриншот ёки файл)* шу ботга юборинг. Текширилгандан сўнг китоб ва бонус жадвал шу ернинг ўзида очилади."
    )

    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['photo', 'document'])
def handle_receipt(message):
    user = message.from_user
    user_info = f"@{user.username}" if user.username else f"ID: {user.id}"

    if ADMIN_ID == 0:
        bot.reply_to(message, "Админ созламаси ҳали якунланмаган. Кейинроқ уриниб кўринг.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton("✅ Тасдиқлаш", callback_data=f"approve:{user.id}")
    btn_reject = types.InlineKeyboardButton("❌ Рад этиш", callback_data=f"reject:{user.id}")
    markup.add(btn_approve, btn_reject)

    caption = (
        f"🧾 *Янги тўлов чеки!*\n"
        f"Мижоз: {user.first_name} ({user_info})\n"
        f"ID: `{user.id}`"
    )

    if message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')

    bot.reply_to(message, "⏳ Чекингиз қабул қилинди! Текширувдан сўнг китоб ва бонус ҳаволалари юборилади.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve:", "reject:")))
def handle_admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Бу амал фақат админ учун.", show_alert=True)
        return

    action, target_id_str = call.data.split(":", 1)
    target_id = int(target_id_str)

    if action == "approve":
        send_book_and_bonus(target_id)
        bot.answer_callback_query(call.id, "Тасдиқланди ва мижозга юборилди!")
        new_caption = (call.message.caption or "") + "\n\n✅ *ТАСДИҚЛАНДИ*"
    else:
        bot.send_message(
            target_id,
            "❌ Тўлов чеки тасдиқланмади. Илтимос, чекни қайта юборинг ёки савол бўлса шу ерга ёзинг."
        )
        bot.answer_callback_query(call.id, "Рад этилди.")
        new_caption = (call.message.caption or "") + "\n\n❌ *РАД ЭТИЛДИ*"

    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=new_caption, parse_mode='Markdown')
        elif call.message.content_type == 'document':
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=new_caption, parse_mode='Markdown')
    except Exception:
        pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text and message.text.startswith('/'):
        return

    user = message.from_user
    user_info = f"@{user.username}" if user.username else f"ID: {user.id}"

    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            f"✉️ *Мижоздан хабар:*\nКимдан: {user.first_name} ({user_info})\nМатн: {message.text}",
            parse_mode='Markdown'
        )
    bot.reply_to(message, "Тўлов маълумотларини кўриш учун /start буйруғини босинг ёки чек расмини юборинг.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    print("Бот ва веб-сервер ишга тушди...")
    bot.infinity_polling(none_stop=True)
