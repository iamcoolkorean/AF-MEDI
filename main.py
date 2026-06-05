import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start, mode_selection
from handlers.triage import handle_triage_message
from handlers.lifestyle import handle_lifestyle_message
from handlers.booking import booking_handler
from sessions import get_session

# Flask 앱 생성 (Render가 포트를 감지해서 sleep 방지)
app = Flask(__name__)

@app.route('/health')
def health():
    return "✅ MEDI+ bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 텔레그램 메시지 핸들러
async def handle_message(update, context):
    user_id = update.effective_user.id
    session = get_session(user_id)
    text = update.message.text.strip()

    if session["mode"] == "triage" and not session["triage_done"]:
        await handle_triage_message(update, context, session, text)
    elif session["mode"] == "lifestyle":
        await handle_lifestyle_message(update, context, session, text)
    else:
        await update.message.reply_text("먼저 /start 를 눌러 모드를 선택해주세요.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return

    # Flask를 별도 스레드에서 실행 (포트 바인딩)
    threading.Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask health server started on port", os.environ.get("PORT", 10000))

    # 텔레그램 봇 Application
    app_tg = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CallbackQueryHandler(mode_selection, pattern="^mode_"))
    app_tg.add_handler(CallbackQueryHandler(booking_handler, pattern="^(book_|cancel_booking)"))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✈️ MEDI+ 텔레그램 봇 실행 중...")
    app_tg.run_polling()

if __name__ == "__main__":
    main()
