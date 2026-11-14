import os
import html
from flask import Flask
from threading import Thread
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
CARD_NUMBER = os.environ.get('CARD_NUMBER', '9860010119822228')
CARD_OWNER = os.environ.get('CARD_OWNER', 'Umar Berdiev')
BOOK_PRICE = os.environ.get('BOOK_PRICE', '29000')

bot = telebot.TeleBot(TOKEN)

BOOK_LINK = "https://docs.google.com/document/d/1t-nOP2ymUKZsAWFz9OV9KPSvMO6zol7Js9YyqoOiD40/edit?usp=drivesdk"
BONUS_SHEET_LINK = "https://docs.google.com/spreadsheets/d/12t7vV5iAvazFr2n4-rg9wIOUMFkXEp8sVaVXJEw2VVw/edit?usp=drivesdk"

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET', 'HEAD', 'POST'])
@app.route('/<path:path>', methods=['GET', 'HEAD', 'POST'])
def catch_all(path):
    return "Bot is running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def send_book_and_bonus(chat_id):
    text = (
        "🎉 <b>Тўловингиз тасдиқланди!</b>\n\n"
        "📖 <b>«Қоғозбозликдан рақамли тизимларга»</b> амалий қўлланмаси ва бонус жадвалингиз тайёр.\n"
        "Қуйидаги тугмалар орқали очиб, ўзингизнинг Google Drive'ингизга нусха олиб ишлатишингиз мумкин:"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_book = types.InlineKeyboardButton("📖 Китобни ўқиш (Google Docs)", url=BOOK_LINK)
    btn_bonus = types.InlineKeyboardButton("📊 Бонус Жадвал (Google Sheets)", url=BONUS_SHEET_LINK)
    markup.add(btn_book, btn_bonus)
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    safe_name = html.escape(message.from_user.first_name or "дўст")
    safe_price = html.escape(BOOK_PRICE)
    safe_card = html.escape(CARD_NUMBER)
    safe_owner = html.escape(CARD_OWNER)

    welcome_text = (
        f"Ассалому алайкум, {safe_name}!\n\n"
        f"📖 <b>«Қоғозбозликдан рақамли тизимларга»</b> амалий қўлланмаси + бонус <b>«Молиявий Назорат Жадвали»</b> (Google Sheets).\n\n"
        f"💰 <b>Нархи:</b> {safe_price}\n"
        f"💳 <b>Тўлов учун карта:</b> <code>{safe_card}</code>\n"
        f"👤 <b>Карта эгаси:</b> {safe_owner}\n\n"
        f"Тўловни амалга оширгач, <b>чек расмини ёки PDF файлини</b> шу ботга юборинг. Текширилгандан сўнг китоб ва бонус жадвал шу ернинг ўзида очилади."
    )

    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

@bot.message_handler(content_types=['photo', 'document'])
def handle_receipt(message):
    user = message.from_user
    safe_first = html.escape(user.first_name or "Фойдаланувчи")
    user_info = f"@{html.escape(user.username)}" if user.username else f"ID: {user.id}"

    if ADMIN_ID == 0:
        bot.reply_to(message, "Админ созламаси ҳали якунланмаган. Кейинроқ уриниб кўринг.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton("✅ Тасдиқлаш", callback_data=f"approve:{user.id}")
    btn_reject = types.InlineKeyboardButton("❌ Рад этиш", callback_data=f"reject:{user.id}")
    markup.add(btn_approve, btn_reject)

    caption = (
        f"🧾 <b>Янги тўлов чеки!</b>\n"
        f"Мижоз: {safe_first} ({user_info})\n"
        f"ID: <code>{user.id}</code>"
    )

    if message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=markup, parse_mode='HTML')

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
        new_caption = (call.message.caption or "") + "\n\n✅ <b>ТАСДИҚЛАНДИ</b>"
    else:
        bot.send_message(
            target_id,
            "❌ Тўлов чеки тасдиқланмади. Илтимос, чекни қайта юборинг ёки савол бўлса шу ерга ёзинг."
        )
        bot.answer_callback_query(call.id, "Рад этилди.")
        new_caption = (call.message.caption or "") + "\n\n❌ <b>РАД ЭТИЛДИ</b>"

    try:
        if call.message.content_type in ('photo', 'document'):
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=new_caption, parse_mode='HTML')
    except Exception:
        pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text and message.text.startswith('/'):
        return

    user = message.from_user
    safe_first = html.escape(user.first_name or "Фойдаланувчи")
    user_info = f"@{html.escape(user.username)}" if user.username else f"ID: {user.id}"
    safe_text = html.escape(message.text or "")

    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            f"✉️ <b>Мижоздан хабар:</b>\nКимдан: {safe_first} ({user_info})\nМатн: {safe_text}",
            parse_mode='HTML'
        )
    bot.reply_to(message, "Тўлов маълумотларини кўриш учун /start буйруғини босинг ёки чек расмини ёки PDF файлини юборинг.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    print("Бот ва веб-сервер ишга тушди...")
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
