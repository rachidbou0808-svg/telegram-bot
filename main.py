import os
import telebot
from groq import Groq

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

def send_long_message(chat_id, text, max_length=4000):
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message,
        "👋 مرحباً! أنا مساعدك الذكي.\n"
        "أرسل لي أي موضوع وسأقدم لك تقريراً شاملاً. 📊"
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_topic = message.text.strip()
    bot.reply_to(message, f"⏳ جاري التحليل حول: {user_topic}\nانتظر لحظة...")
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في تقديم تقارير شاملة باللغة العربية."},
                {"role": "user", "content": f"اكتب تقريراً شاملاً ومفصلاً باللغة العربية حول: {user_topic}"}
            ]
        )
        result = response.choices[0].message.content
        bot.send_message(message.chat.id, "✅ اكتمل التقرير:")
        send_long_message(message.chat.id, result)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ:\n{str(e)}")

print("✅ البوت يعمل...")
bot.infinity_polling(timeout=30, long_polling_timeout=10)
