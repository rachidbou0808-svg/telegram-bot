import os
import telebot
from crewai import Agent, Task, Crew, Process

# ══════════════════════════════════════════
#   جلب المفاتيح تلقائياً من بيئة تشغيل سيرفر Railway
# ══════════════════════════════════════════
os.environ["GROQ_API_KEY"] = os.environ.get('GROQ_API_KEY')
TELEGRAM_TOKEN             = os.environ.get('TELEGRAM_TOKEN')
# ══════════════════════════════════════════

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ─── تعريف العميل الذكي ──────────────────
researcher_agent = Agent(
    role="محلل بيانات محترف",
    goal="تقديم تقارير دقيقة وشاملة باللغة العربية",
    backstory=(
        "أنت خبير في تحليل المعلومات وتقديمها بأسلوب واضح ومنظم. "
        "تساعد المستخدمين في الحصول على معلومات موثوقة وشاملة."
    ),
    allow_delegation=False,
    verbose=True,
    llm="groq/llama3-70b-8192",

# ─── تقسيم الرسائل الطويلة ───────────────
def send_long_message(chat_id, text, max_length=4000):
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

# ─── أوامر البداية ───────────────────────
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 مرحباً! أنا مساعدك الذكي.\n\n"
        "📌 أرسل لي أي موضوع وسأقدم لك تقريراً شاملاً عنه."
    )

# ─── استقبال الرسائل ─────────────────────
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_topic = message.text.strip()
    bot.reply_to(message, f"⏳ جاري التحليل حول:\n*{user_topic}*\n\nانتظر لحظة...", parse_mode="Markdown")

    try:
        research_task = Task(
            description=(
                f"اكتب تقريراً شاملاً ومفصّلاً باللغة العربية حول:\n{user_topic}\n\n"
                "يجب أن يحتوي على:\n"
                "1. مقدمة موجزة\n"
                "2. النقاط الرئيسية\n"
                "3. تفاصيل مهمة\n"
                "4. خلاصة واضحة"
            ),
            expected_output="تقرير شامل ومنظم باللغة العربية بعناوين وتفاصيل واضحة.",
            agent=researcher_agent,
        )

        crew = Crew(agents=[researcher_agent], tasks=[research_task], process=Process.sequential)
        result = crew.kickoff()
        bot.send_message(message.chat.id, "✅ اكتمل التقرير:")
        send_long_message(message.chat.id, str(result))

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ:\n`{str(e)}`", parse_mode="Markdown")

if __name__ == "__main__":
    print("🚀 البوت يعمل بنجاح على سيرفر Railway...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
    
