import re
from telegram import Update
from telegram.ext import ContextTypes
from sessions import get_session
from prompts import LIFESTYLE_SYSTEM_PROMPT
from gemini_api import generate_response
from database import MOCK_SOLDIERS
from utils import soldier_data_to_text, send_long_message   # ← 분할 전송 함수

async def handle_lifestyle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict, user_text: str):
    # 군번 패턴 감지
    match = re.search(r'\d{2}-\d{8}', user_text)
    soldier_data = None
    if match:
        snum = match.group(0)
        if snum in MOCK_SOLDIERS:
            soldier_data = MOCK_SOLDIERS[snum]
            session["soldier_id"] = snum
        else:
            await update.message.reply_text("등록되지 않은 군번입니다.")
            return

    enriched_prompt = LIFESTYLE_SYSTEM_PROMPT
    if soldier_data:
        enriched_prompt += soldier_data_to_text(snum, soldier_data)

    history = session.get("history", [])
    history.append({"role": "user", "parts": [user_text]})

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        ai_response = generate_response(enriched_prompt, history)
    except Exception as e:
        await update.message.reply_text(f"🚨 시스템 오류: {str(e)[:200]}")
        return

    history.append({"role": "model", "parts": [ai_response]})
    session["history"] = history

    # 긴 응답은 자동 분할 전송
    await send_long_message(update, context, ai_response)
