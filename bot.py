import os
import threading
from flask import Flask
import telebot
from telebot import types

# Environment Variables (Render'дан олинади)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
CARD_NUMBER = os.environ.get("CARD_NUMBER", "8600 0000 0000 0000")
CARD_HOLDER = os.environ.get("CARD_HOLDER", "UMAR BERDIYEV")
BOOK_PRICE = os.environ.get("BOOK_PRICE", "49 000 сўм")

# Китоб PDF файли ва бонус жадвал ҳаволаси
BOOK_PDF_PATH = "Qogozbozlikdan_raqamli_tizimga_KITOB_2.pdf"
BONUS_SHEET_URL = "https://docs.google.com/spreadsheets/d/12t7vV5iAvazFr2n4-rg9wIOUMFkXEp8sVaVXJEw2VVw/edit?usp=drivesdk"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


# Render ва UptimeRobot учун веб-сервер (200 OK)
@app.route("/", defaults={"path": ""}, methods=["GET", "HEAD", "POST"])
@app.route("/<path:path>", methods=["GET", "HEAD", "POST"])
def catch_all(path):
    return "Bot is running!", 200


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


# 1. /start буйруғи
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_buy = types.InlineKeyboardButton("💳 Китобни харид қилиш", callback_data="buy_book")
    btn_about = types.InlineKeyboardButton("📘 Китоб ҳақида маълумот", callback_data="about_book")
    markup.add(btn_buy, btn_about)

    text = (
        f"Ассалому алайкум, {message.from_user.first_name}! 👋\n\n"
        "<b>«Қоғозбозликдан рақамли тизимга»</b> — кичик бизнесни 30 кунда "
        "Google Sheets ва Telegram ёрдамида автоматлаштириш бўйича амалий қўлланма.\n\n"
        f"💰 <b>Нархи:</b> {BOOK_PRICE}\n"
        "🎁 <b>Бонус:</b> Тайёр «Молиявий Назорат ва Бошқарув Жадвали» шаблони!\n\n"
        "Харид қилиш учун қуйидаги тугмани босинг:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


# 2. Китоб ҳақида маълумот ва тўлов реквизитлари
@bot.callback_query_handler(func=lambda call: call.data in ["about_book", "buy_book"])
def handle_info_and_buy(call):
    bot.answer_callback_query(call.id)

    if call.data == "about_book":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Китобни харид қилиш", callback_data="buy_book"))
        info_text = (
            "📘 <b>Қўлланма ичида нималар бор?</b>\n\n"
            "• 7 та амалий боб ва Ўзбекистон бозоридаги реал кейслар;\n"
            "• «Ақлли касса», Mini-CRM, Омбор ва KPI жадвал формулалари;\n"
            "• Соат 21:00 да Telegram'га автоматик ҳисобот юборувчи скрипт;\n"
            "• 30 кунлик трансформация харитаси ва тайёр бонус шаблон."
        )
        bot.send_message(call.message.chat.id, info_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "buy_book":
        pay_text = (
            "💳 <b>Тўлов маълумотлари:</b>\n\n"
            f"Карта рақами: <code>{CARD_NUMBER}</code>\n"
            f"Карта эгаси: <b>{CARD_HOLDER}</b>\n"
            f"Тўлов суммаси: <b>{BOOK_PRICE}</b>\n\n"
            "📸 Тўловни амалга оширгач, <b>чек расмини ёки PDF-квитанциясини</b> "
            "шу ботга юборинг. Админ тасдиқлаши билан китоб ва бонус жадвал автоматик юборилади."
        )
        bot.send_message(call.message.chat.id, pay_text, parse_mode="HTML")


# 3. Мижоздан чек қабул қилиш (расм ёки PDF/ҳужжат)
@bot.message_handler(content_types=["photo", "document"])
def handle_receipt(message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Йўқ"

    caption = (
        "🧾 <b>Янги тўлов чеки келди!</b>\n\n"
        f"👤 Мижоз: {user.first_name} (ID: <code>{user.id}</code>)\n"
        f"🔗 Username: {username}"
    )

    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton("✅ Тасдиқлаш", callback_data=f"approve_{user.id}")
    btn_reject = types.InlineKeyboardButton("❌ Рад этиш", callback_data=f"reject_{user.id}")
    admin_markup.add(btn_approve, btn_reject)

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id, caption=caption, parse_mode="HTML", reply_markup=admin_markup)
    else:
        file_id = message.document.file_id
        bot.send_document(ADMIN_ID, file_id, caption=caption, parse_mode="HTML", reply_markup=admin_markup)

    bot.reply_to(
        message,
        "✅ Чекингиз қабул қилинди ва текшириш учун админга юборилди.\n"
        "Тасдиқлангач, китоб шу ерга юборилади. Илтимос, бироз кутинг."
    )


# 4. Админ томонидан тасдиқлаш ёки рад этиш
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Бу тугма фақат админ учун!", show_alert=True)
        return

    action, user_id_str = call.data.split("_", 1)
    target_user_id = int(user_id_str)

    if action == "approve":
        if not os.path.exists(BOOK_PDF_PATH):
            bot.answer_callback_query(call.id, "⚠️ PDF файл топилмади!", show_alert=True)
            bot.send_message(ADMIN_ID, f"❌ Хатолик: <code>{BOOK_PDF_PATH}</code> файли GitHub репозиторияда топилмади.", parse_mode="HTML")
            return

        bonus_markup = types.InlineKeyboardMarkup()
        bonus_markup.add(
            types.InlineKeyboardButton("📊 Молиявий Назорат Жадвали (Бонус)", url=BONUS_SHEET_URL)
        )

        success_caption = (
            "🎉 <b>Тўловингиз тасдиқланди! Харидингиз учун раҳмат!</b>\n\n"
            "📘 Юқоридаги PDF файл — <b>«Қоғозбозликдан рақамли тизимга»</b> тўлиқ қўлланмаси (25 саҳифа).\n"
            "🎁 Китоб охирида ва қуйидаги тугма орқали тайёр <b>Google Sheets бонус жадвалини</b> очиб, "
            "<i>Файл → Нусха яратиш</i> орқали ўзингизга сақлаб олишингиз мумкин:"
        )

        with open(BOOK_PDF_PATH, "rb") as pdf_file:
            bot.send_document(
                target_user_id,
                pdf_file,
                caption=success_caption,
                parse_mode="HTML",
                reply_markup=bonus_markup
            )

        bot.answer_callback_query(call.id, "✅ Китоб мижозга юборилди!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n✅ <b>ТАСДИҚЛАНДИ (Китоб юборилди)</b>",
            parse_mode="HTML"
        )

    elif action == "reject":
        bot.send_message(
            target_user_id,
            "❌ Юборилган чек тасдиқланмади. Илтимос, тўлов маълумотларини текшириб, "
            "чекни қайта юборинг ёки админ билан боғланинг."
        )
        bot.answer_callback_query(call.id, "❌ Рад этилди!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n❌ <b>РАД ЭТИЛДИ</b>",
            parse_mode="HTML"
        )


if __name__ == "__main__":
    print("Бот ва веб-сервер ишга тушди...")
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
