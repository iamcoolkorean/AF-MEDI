import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sessions import get_session
from prompts import TRIAGE_SYSTEM_PROMPT
from gemini_api import generate_response
from config import MEDIC_PHONE_SLOTS, DOCTOR_SLOTS
from utils import send_long_message, generate_preliminary_chart

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
        
        # 1. 결과 파싱
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

        # 2. 사용자 이름 찾기 (세션에서 또는 첫 메시지에서 추출)
        soldier_name = session.get("soldier_name", "알 수 없음")
        if soldier_name == "알 수 없음":
            # 첫 사용자 메시지에서 이름을 추출 시도
            first_msg = session["history"][0]["parts"][0] if session["history"] else ""
            name_match = re.search(r'(병장|상병|일병|이병)\s+(\S+)', first_msg)
            if name_match:
                soldier_name = name_match.group(2)

        # 3. 예비 문진표 생성
        chart_message = await generate_preliminary_chart(soldier_name, session["history"])

        # 4. Level에 따른 분기
        if level == 1:
            # 경증: 군의관 전화 진료
            keyboard = [[InlineKeyboardButton(f"📞 {t}", callback_data=f"book_medic_{t}")] for t in MEDIC_PHONE_SLOTS]
            keyboard.append([InlineKeyboardButton("취소", callback_data="cancel_booking")])
            
            await update.message.reply_text(
                f"필승! 📋 **AI 예진 결과 (Level 1 - 경증)**\n\n{desc}\n\n💡 {rec}\n\n군의관 전화상담 예약 시간을 선택하세요.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            # 예비 문진표 전송
            await send_long_message(update, context, chart_message)

        elif level == 2:
            # 중등증: 대면 진료
            keyboard = [[InlineKeyboardButton(f"🏥 {t}", callback_data=f"book_doctor_{t}")] for t in DOCTOR_SLOTS]
            keyboard.append([InlineKeyboardButton("취소", callback_data="cancel_booking")])
            
            care_guide = ("\n\n[진료 전 행동 요령]\n"
                          "- 충분한 휴식을 취하세요.\n"
                          "- 증상이 심해지면 즉시 응급실로 방문하세요.\n"
                          "- [자가 모니터링 체크리스트]\n"
                          "  1) 체온 측정 (1시간 간격)\n"
                          "  2) 통증 강도 기록 (0~10)\n"
                          "  3) 의식 상태 체크 (멍함/정상)\n")
            
            await update.message.reply_text(
                f"필승! 📋 **AI 예진 결과 (Level 2 - 중등증/중증의심)**\n\n{desc}\n\n💡 {rec}{care_guide}\n\n대면 진료 예약 시간을 선택하세요.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            # 예비 문진표 전송
            await send_long_message(update, context, chart_message)

        elif level == 3:
            # 중증 응급: 즉시 내원/출동
            emergency_alert = ("🚨 **응급 상황 발령 (Level 3)** 🚨\n\n"
                               f"{desc}\n\n"
                               "**즉시 의무대 출동 또는 내원을 요청합니다!**\n"
                               "부대 상황병에게 자동 알림이 전파되었습니다.\n"
                               "구급대가 출동 중이오니, 환자를 절대 혼자 두지 마십시오.")
            await update.message.reply_text(emergency_alert)
            # 세션 초기화
            session["mode"] = None
        else:
            await update.message.reply_text("분류 오류가 발생했습니다. 다시 시도해 주십시오.")
            session["mode"] = None
    else:
        # 문진 중일 때는 AI 질문을 그대로 출력
        await send_long_message(update, context, ai_response)
