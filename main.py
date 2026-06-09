import os
import telebot
from crewai import Agent, Task, Crew, Process

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

researcher_agent = Agent(
    role="محلل بيانات محترف",
    goal="تقديم تقارير دقيقة وشاملة باللغة العربية",
    backstory="أنت خبير في تحليل المعلومات وتقديمها بأسلوب واضح ومنظم.",
    allow_delegation=False,
    verbose=True,
    llm="groq/llama-3.3-70b-versatile",
)

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
        research_task = Task(
            description=(
                f"اكتب تقريراً شاملاً باللغة العربية حول:\n{user_topic}\n\n"
                "يحتوي على: مقدمة، نقاط رئيسية، تفاصيل، وخلاصة."
            ),
            expected_output="تقرير منظم باللغة العربية بعناوين وتفاصيل واضحة.",
            agent=researcher_agent,
        )
        crew = Crew(
            agents=[researcher_agent],
            tasks=[research_task],
            process=Process.sequential,
        )
        result = crew.kickoff()
        bot.send_message(message.chat.id, "✅ اكتمل التقرير:")
        send_long_message(message.chat.id, str(result))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ:\n{str(e)}")

print("✅ البوت يعمل...")
bot.infinity_polling(timeout=30, long_polling_timeout=10)
