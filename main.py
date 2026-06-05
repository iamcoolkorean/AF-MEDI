from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start, mode_selection
from handlers.triage import handle_triage_message
from handlers.lifestyle import handle_lifestyle_message
from handlers.booking import booking_handler
from sessions import get_session

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

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mode_selection, pattern="^mode_"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^(book_|cancel_booking)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✈️ MEDI+ 텔레그램 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
