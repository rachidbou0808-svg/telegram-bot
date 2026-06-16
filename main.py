import os
import telebot
import base64
import requests
import tempfile
from groq import Groq
from telebot import types

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')

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
        types.KeyboardButton("🌤️ الطقس"),
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
        "🎤 الرسائل الصوتية\n"
        "🌤️ الطقس\n"
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
        "/price - أسعار العملات\n"
        "/weather [مدينة] - الطقس\n\n"
        "*ما يمكنني فعله:*\n"
        "🖼️ أصف وأحلل الصور\n"
        "📄 ألخص ملفات PDF\n"
        "🔗 ألخص محتوى الروابط\n"
        "🎤 أحول الصوت إلى نص\n"
        "🌤️ أعطيك الطقس\n"
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

@bot.message_handler(commands=["weather"])
def weather_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "🌤️ اكتب اسم المدينة:\nمثال: /weather الجزائر")
        return
    city = parts[1]
    get_weather(message.chat.id, city)

def get_weather(chat_id, city):
    bot.send_message(chat_id, f"⏳ جاري جلب طقس {city}...")
    try:
        if WEATHER_API_KEY:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ar"
            response = requests.get(url)
            data = response.json()
            if data.get("cod") == 200:
                temp = data["main"]["temp"]
                feels = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                desc = data["weather"][0]["description"]
                wind = data["wind"]["speed"]
                result = (
                    f"🌤️ *طقس {city}*\n\n"
                    f"🌡️ الحرارة: {temp}°C\n"
                    f"🤔 تبدو كأنها: {feels}°C\n"
                    f"💧 الرطوبة: {humidity}%\n"
                    f"💨 الرياح: {wind} م/ث\n"
                    f"📋 الحالة: {desc}"
                )
                bot.send_message(chat_id, result, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ لم أجد مدينة بهذا الاسم: {city}")
        else:
            result = ask_groq(f"أعطني معلومات عن الطقس المعتاد في مدينة {city} في هذا الوقت من السنة.")
            bot.send_message(chat_id, f"🌤️ *معلومات عن طقس {city}:*\n\n{result}", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

@bot.message_handler(conte
