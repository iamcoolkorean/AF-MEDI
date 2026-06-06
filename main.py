import os
import sys
import asyncio
import threading
from flask import Flask
from telegram import Bot
from telegram.error import InvalidToken
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start, mode_selection
from handlers.triage import handle_triage_message
from handlers.lifestyle import handle_lifestyle_message
from handlers.booking import booking_handler
from sessions import get_session

app = Flask(__name__)

@app.route('/health')
def health():
    return "✅ MEDI+ bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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

async def validate_token(token: str) -> bool:
    try:
        bot = Bot(token=token)
        await bot.get_me()
        return True
    except InvalidToken:
        return False
    except Exception:
        return False

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    threading.Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask health server started on port", os.environ.get("PORT", 10000))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if not loop.run_until_complete(validate_token(TELEGRAM_BOT_TOKEN)):
        print("❌ TELEGRAM_BOT_TOKEN이 유효하지 않습니다. BotFather에서 새 토큰을 발급받아 Render 환경변수를 업데이트하세요.")
        sys.exit(1)
    print("✅ 텔레그램 토큰 검증 완료")

    app_tg = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CallbackQueryHandler(mode_selection, pattern="^mode_"))
    app_tg.add_handler(CallbackQueryHandler(booking_handler, pattern="^(book_|cancel_booking)"))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✈️ MEDI+ 텔레그램 봇 실행 중...")
    try:
        app_tg.run_polling()
    except InvalidToken:
        print("❌ 런타임 중 토큰이 거부되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    finally:
        print("🛬 MEDI+ 봇 종료")

if __name__ == "__main__":
    main()
