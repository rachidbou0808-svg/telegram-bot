import os
import telebot
import anthropic

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def send_long_message(chat_id, text, max_length=4000):
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message,
        "👋 مرحباً! أنا مساعدك الذكي.\n"
        "📌 أرسل لي أي موضوع وسأقدم لك تقريراً شاملاً عنه."
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_topic = message.text.strip()
    bot.reply_to(message, f"⏳ جاري التحليل حول: {user_topic}\nانتظر لحظة...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"أنت مساعد ذكي متخصص في تقديم تقارير شاملة باللغة العربية. اكتب تقريراً شاملاً ومفصلاً باللغة العربية حول: {user_topic}"
                }
            ]
        )

        result = response.content[0].text
    bot.send_message(message.chat.id, "✅ اكتمل التقرير:")
        send_long_message(message.chat.id, result)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ:\n{str(e)}")

print("✅ البوت يعمل...")
bot.infinity_polling(timeout=30, long_polling_timeout=10)

