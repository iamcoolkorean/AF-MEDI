import re
from telegram import Update
from telegram.ext import ContextTypes
from sessions import get_session
from prompts import LIFESTYLE_SYSTEM_PROMPT
from gemini_api import generate_response
from database import MOCK_SOLDIERS
from utils import soldier_data_to_text, send_long_message, MOCK_MEAL_MENU

async def handle_lifestyle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict, user_text: str):
    # 군번 패턴 감지
    match = re.search(r'\d{2}-\d{8}', user_text)
    soldier_data = None
    meal_context = ""
    
    if match:
        snum = match.group(0)
        if snum in MOCK_SOLDIERS:
            soldier_data = MOCK_SOLDIERS[snum]
            session["soldier_id"] = snum
            # 군번만 입력하고 다른 말이 없으면 바로 건강검진 분석 요청
            if user_text.strip() == snum or len(user_text) < 20:
                user_text = "건강검진 결과 분석해줘"
        else:
            await update.message.reply_text("등록되지 않은 군번입니다.")
            return

    # 급식/영양제 키워드 감지 시 목업 급식 데이터 추가
    if any(keyword in user_text for keyword in ["급식", "식단", "영양제", "추천"]):
        meal_items = "\n".join([f"- {k}: {v}" for k, v in MOCK_MEAL_MENU.items()])
        meal_context = f"\n\n[오늘의 부대 급식 메뉴]\n{meal_items}"

    enriched_prompt = LIFESTYLE_SYSTEM_PROMPT
    if soldier_data:
        enriched_prompt += soldier_data_to_text(snum, soldier_data)
    if meal_context:
        enriched_prompt += meal_context

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
