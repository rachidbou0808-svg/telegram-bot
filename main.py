import os
import telebot
import anthropic
import base64
import requests
from telebot import types

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ========================
# دوال مساعدة
# ========================
def send_long_message(chat_id, text, max_length=4000):
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

def ask_claude(prompt, system="أنت مساعد ذكي يتحدث العربية. أجب بشكل واضح ومفيد."):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def ask_claude_with_image(image_base64, media_type, prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return response.content[0].text

def download_file(file_id):
    file_info = bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
    response = requests.get(url)
    return response.content

# ========================
# القائمة الرئيسية
# ========================
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

# ========================
# /start
# ========================
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

# ========================
# /help
# ========================
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
        "😄 أترجم الستيكرات"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=main_menu())

# ========================
# /news
# ========================
@bot.message_handler(commands=["news"])
def news_command(message):
    bot.send_message(message.chat.id, "⏳ جاري جلب الأخبار...")
    try:
        result = ask_claude("أعطني ملخصاً لأهم الأخبار العالمية والعربية اليوم في نقاط واضحة.")
        bot.send_message(message.chat.id, "📰 *آخر الأخبار:*", parse_mode="Markdown")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

# ========================
# /price
# ========================
@bot.message_handler(commands=["price"])
def price_command(message):
    bot.send_message(message.chat.id, "⏳ جاري جلب الأسعار...")
    try:
        result = ask_claude("أعطني معلومات عن أسعار العملات الرئيسية مقابل الدولار وأسعار البيتكوين والذهب تقريباً.")
        bot.send_message(message.chat.id, "💰 *أسعار العملات:*", parse_mode="Markdown")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

# ========================
# معالج الصور
# ========================
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, "🖼️ جاري تحليل الصورة...")
    try:
        photo = message.photo[-1]
        file_data = download_file(photo.file_id)
        image_base64 = base64.standard_b64encode(file_data).decode("utf-8")
        caption = message.caption or "صف هذه الصورة بالتفصيل باللغة العربية"
        result = ask_claude_with_image(image_base64, "image/jpeg", caption)
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في تحليل الصورة: {str(e)}")

# ========================
# معالج الملفات PDF
# ========================
@bot.message_handler(content_types=["document"])
def handle_document(message):
    bot.send_chat_action(message.chat.id, 'typing')
    doc = message.document
    if doc.mime_type == "application/pdf":
        bot.reply_to(message, "📄 جاري قراءة الملف...")
        try:
            file_data = download_file(doc.file_id)
            pdf_base64 = base64.standard_b64encode(file_data).decode("utf-8")
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            }
                        },
                        {"type": "text", "text": "لخص هذا الملف بالعربية بشكل شامل ومفيد."}
                    ]
                }]
            )
            result = response.content[0].text
            bot.send_message(message.chat.id, "📄 *ملخص الملف:*", parse_mode="Markdown")
            send_long_message(message.chat.id, result)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")
    else:
        bot.reply_to(message, "⚠️ حالياً أدعم ملفات PDF فقط.")

# ========================
# معالج الستيكرات
# ========================
@bot.message_handler(content_types=["sticker"])
def handle_sticker(message):
    emoji = message.sticker.emoji or "😊"
    try:
        result = ask_claude(f"أرسل لي شخص ستيكر يعبر عن {emoji}. اكتب رداً مناسباً وطريفاً باللغة العربية.")
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, "😄 ستيكر جميل!")

# ========================
# معالج الرسائل النصية
# ========================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.strip()

    # الأزرار
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

    # رابط
    if text.startswith("http://") or text.startswith("https://"):
        bot.send_chat_action(message.chat.id, 'typing')
        bot.reply_to(message, "🔗 جاري تحليل الرابط...")
        try:
            result = ask_claude(f"لخص محتوى هذا الرابط باللغة العربية: {text}")
            send_long_message(message.chat.id, result)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")
        return

    # رسالة عادية
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        result = ask_claude(f"أنت مساعد ذكي متخصص. أجب على هذا باللغة العربية بشكل مفيد وشامل: {text}")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

print("✅ البوت يعمل...")
bot.infinity_polling(timeout=30, long_polling_timeout=10)
        
