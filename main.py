import os
import telebot
import base64
import requests
from groq import Groq
from telebot import types

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

def send_long_message(chat_id, text, max_length=4000):
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

def ask_groq(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "أنت مساعد ذكي يتحدث العربية بطلاقة. أجب بشكل واضح ومفيد."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024
    )
    return response.choices[0].message.content

def download_file(file_id):
    file_info = bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
    response = requests.get(url)
    return response.content

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 تقرير شامل"),
        types.KeyboardButton("📰 آخر الأخبار"),
        types.KeyboardButton("💰 أسعار العملات"),
        types.KeyboardButton("🤖 اسأل الذكاء الاصطناعي"),
        types.KeyboardButton("ℹ️ مساعدة")
    )
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    name = message.from_user.first_name
    bot.send_message(
        message.chat.id,
        f"👋 أهلاً {name}!\n\n"
        "أنا مساعدك الذكي 🤖\n\n"
        "أستطيع التعامل مع:\n"
        "📝 الرسائل النصية\n"
        "🖼️ الصور\n"
        "📄 ملفات PDF\n"
        "🔗 الروابط\n"
        "😄 الستيكرات\n\n"
        "اختر من القائمة أو أرسل أي شيء!",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=["help"])
def send_help(message):
    help_text = (
        "📖 *الأوامر المتاحة:*\n\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/news - آخر الأخبار\n"
        "/price - أسعار العملات\n\n"
        "*ما يمكنني فعله:*\n"
        "🖼️ أصف وأحلل الصور\n"
        "📄 ألخص ملفات PDF\n"
        "🔗 ألخص محتوى الروابط\n"
        "📝 أجيب على أي سؤال\n"
        "😄 أرد على الستيكرات"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=["news"])
def news_command(message):
    bot.send_message(message.chat.id, "⏳ جاري جلب الأخبار...")
    try:
        result = ask_groq("أعطني ملخصاً لأهم الأخبار العالمية والعربية اليوم في نقاط واضحة.")
        bot.send_message(message.chat.id, "📰 *آخر الأخبار:*", parse_mode="Markdown")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

@bot.message_handler(commands=["price"])
def price_command(message):
    bot.send_message(message.chat.id, "⏳ جاري جلب الأسعار...")
    try:
        result = ask_groq("أعطني معلومات عن أسعار العملات الرئيسية مقابل الدولار وأسعار البيتكوين والذهب تقريباً.")
        bot.send_message(message.chat.id, "💰 *أسعار العملات:*", parse_mode="Markdown")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, "🖼️ جاري تحليل الصورة...")
    try:
        caption = message.caption or "صف هذه الصورة بالتفصيل باللغة العربية"
        file_id = message.photo[-1].file_id
        image_data = download_file(file_id)
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": caption
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        result = response.choices[0].message.content
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    bot.reply_to(message, "📄 استلمت ملفك! للأسف Groq لا يدعم قراءة PDF مباشرة. جرب أن تنسخ النص وأرسله لي.")

@bot.message_handler(content_types=["sticker"])
def handle_sticker(message):
    emoji = message.sticker.emoji or "😊"
    try:
        result = ask_groq(f"أرسل لي شخص ستيكر يعبر عن {emoji}. اكتب رداً مناسباً وطريفاً باللغة العربية.")
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, "😄 ستيكر جميل!")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.strip()

    if text == "📊 تقرير شامل":
        bot.send_message(message.chat.id, "📊 أرسل لي الموضوع:")
        return
    if text == "📰 آخر الأخبار":
        news_command(message)
        return
    if text == "💰 أسعار العملات":
        price_command(message)
        return
    if text == "🤖 اسأل الذكاء الاصطناعي":
        bot.send_message(message.chat.id, "🤖 اكتب سؤالك:")
        return
    if text == "ℹ️ مساعدة":
        send_help(message)
        return

    if text.startswith("http://") or text.startswith("https://"):
        bot.send_chat_action(message.chat.id, 'typing')
        bot.reply_to(message, "🔗 جاري تحليل الرابط...")
        try:
            result = ask_groq(f"لخص محتوى هذا الرابط باللغة العربية: {text}")
            send_long_message(message.chat.id, result)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    try:
        result = ask_groq(f"أجب على هذا باللغة العربية بشكل مفيد وشامل: {text}")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

print("✅ البوت يعمل...")
bot.infinity_polling(timeout=30, long_polling_timeout=10)
