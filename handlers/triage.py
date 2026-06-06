import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sessions import get_session
from prompts import TRIAGE_SYSTEM_PROMPT
from gemini_api import generate_response
from config import MEDIC_PHONE_SLOTS, DOCTOR_SLOTS
from utils import send_long_message   # ← 분할 전송 함수

async def handle_triage_message(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict, user_text: str):
    session["history"].append({"role": "user", "parts": [user_text]})
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        ai_response = generate_response(TRIAGE_SYSTEM_PROMPT, session["history"])
    except Exception as e:
        await update.message.reply_text(f"🚨 시스템 오류: {str(e)[:200]}")
        return

    session["history"].append({"role": "model", "parts": [ai_response]})

    if "FINAL_RESULT:" in ai_response:
        session["triage_done"] = True
        level = None
        desc = ""
        rec = ""
        for line in ai_response.splitlines():
            if line.startswith("LEVEL:"):
                try: level = int(line.split(":")[1].strip())
                except: pass
            elif line.startswith("DESCRIPTION:"):
                desc = line.split(":",1)[1].strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line.split(":",1)[1].strip()

        if level == 1:
            keyboard = [[InlineKeyboardButton(f"{t}", callback_data=f"book_medic_{t}")] for t in MEDIC_PHONE_SLOTS]
            keyboard.append([InlineKeyboardButton("취소", callback_data="cancel_booking")])
            await update.message.reply_text(
                f"필승! 📋 **AI 예진 결과 (Level 1)**\n\n{desc}\n\n💡 {rec}\n\n의무병 전화상담 예약 가능 시간입니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif level == 2:
            keyboard = [[InlineKeyboardButton(f"{t}", callback_data=f"book_doctor_{t}")] for t in DOCTOR_SLOTS]
            keyboard.append([InlineKeyboardButton("취소", callback_data="cancel_booking")])
            await update.message.reply_text(
                f"필승! 📋 **AI 예진 결과 (Level 2)**\n\n{desc}\n\n💡 {rec}\n\n군의관 원격 진료 가능 시간입니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif level == 3:
            await update.message.reply_text(
                f"🚨 필승! **응급 상황 (Level 3)**\n\n{desc}\n\n{rec}\n\n⚠️ 즉시 응급실로 이동하십시오. 부대 상황병에게도 자동 전파되었습니다."
            )
            session["mode"] = None
        else:
            await update.message.reply_text("분류 오류가 발생했습니다. 다시 시도해 주십시오.")
            session["mode"] = None
    else:
        # 문진 중일 때는 AI 질문을 그대로 출력 (긴 경우 분할 전송)
        await send_long_message(update, context, ai_response)
