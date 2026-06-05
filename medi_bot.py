import os
import re
import random
import threading
from typing import Dict, List

# .env 파일 자동 로드
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== API 키 로테이션 ====================
GEMINI_KEYS = []
for i in range(1, 9):
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if key:
        GEMINI_KEYS.append(key)

if not GEMINI_KEYS:
    print("WARNING: No Gemini API keys found. Using placeholder.")
    GEMINI_KEYS = ["placeholder"]

key_lock = threading.Lock()
current_key_idx = 0

def get_next_key():
    global current_key_idx
    with key_lock:
        key = GEMINI_KEYS[current_key_idx]
        current_key_idx = (current_key_idx + 1) % len(GEMINI_KEYS)
        return key

def generate_with_gemini(system_prompt: str, history: List[dict], model_name: str = "gemini-1.5-flash") -> str:
    key = get_next_key()
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [msg["parts"][0]]})

    response = model.generate_content(contents)
    return response.text

# ==================== 목업 데이터 ====================
MOCK_SOLDIERS = {
    "25-12345678": {
        "이름": "김민수",
        "계급": "병장",
        "검진일": "2025-03-15",
        "결과": {
            "혈압": "135/85 (수축기 고혈압 전단계 주의)",
            "공복혈당": "102 mg/dL (당뇨 전단계)",
            "총콜레스테롤": "210 mg/dL (경계)",
            "AST/ALT": "25/30 (정상)",
            "비타민D": "18 ng/mL (부족)"
        }
    },
    "25-23456789": {
        "이름": "이지훈",
        "계급": "상병",
        "검진일": "2025-03-15",
        "결과": {
            "혈압": "120/80 (정상)",
            "공복혈당": "95 mg/dL (정상)",
            "총콜레스테롤": "180 mg/dL (정상)",
            "AST/ALT": "45/55 (간 수치 약간 상승, 음주/영양 관리 필요)",
            "철분": "55 ug/dL (경계)"
        }
    },
    "25-34567890": {
        "이름": "박성호",
        "계급": "일병",
        "검진일": "2025-03-15",
        "결과": {
            "혈압": "140/90 (고혈압 의심)",
            "공복혈당": "110 mg/dL (당뇨 의심)",
            "총콜레스테롤": "250 mg/dL (높음)",
            "AST/ALT": "35/40 (정상)",
            "체지방률": "28% (높음, 운동 권고)"
        }
    }
}

# ==================== 시스템 프롬프트 ====================
TRIAGE_SYSTEM_PROMPT = """
너는 대한민국 공군 의무대 AI 예진 도우미 'MEDI+'야. 
병사의 증상을 듣고 문진을 진행한 후, 응급도를 분류하여 적절한 진료 경로를 안내해야 해.

[진행 방식]
1. 사용자에게 군번, 계급, 이름, 주요 증상을 물어봐. 
2. 필요한 추가 질문을 한 가지씩만 해라. (예: "통증이 얼마나 지속됐나요?", "열을 재셨나요? 몇 도인가요?")
3. 충분한 정보가 모이면 아래 형식으로 최종 분류를 내려라.

[분류 기준]
- Level 1 (경증): 단순 감기, 소화불량, 가벼운 근육통 → 의무병 전화상담 예약
- Level 2 (중등도): 38℃ 이상 고열, 설사, 피부발진, 중간 강도 통증 → 군의관 원격 진료 예약
- Level 3 (응급 의심): 심한 복통, 흉통, 호흡곤란, 사지 저림, 골절 의심 → 즉시 응급실 내원 (상황병 자동 알림)

[최종 결과 형식]
FINAL_RESULT:
LEVEL: [1/2/3]
DESCRIPTION: [간략한 증상 요약]
RECOMMENDATION: [구체적인 행동 지침]

⚠️ 약물 처방이나 확정 진단은 하지 마. 반드시 의료진의 판단이 필요함을 명시해.
"""

LIFESTYLE_SYSTEM_PROMPT = """
너는 공군 병사들의 건강관리를 도와주는 생활습관 도우미야.
병사들의 건강검진 결과를 바탕으로 설명을 제공하고, 식습관, 운동, 영양, 스트레스 관리 등에 대해 조언해 줘.
검진 결과는 사용자가 군번을 알려주면 제공될 거야.

- 답변은 항상 친절하고 군인에게 적합한 말투로.
- 의학적 확진은 하지 않지만, 예방적 조언은 해도 됨.
- 검진 결과가 없으면 일반 건강 상식으로 답변해.
"""

MEDIC_PHONE_SLOTS = ["10:00", "11:00", "13:30", "14:30", "16:00"]
DOCTOR_SLOTS = ["09:30", "10:30", "14:00", "15:00", "16:00"]

# ==================== 세션 관리 ====================
user_sessions: Dict[int, dict] = {}

def get_session(user_id: int):
    if user_id not in user_sessions:
        user_sessions[user_id] = {"mode": None, "history": [], "soldier_id": None, "triage_done": False}
    return user_sessions[user_id]

# ==================== 텔레그램 핸들러 ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🩺 AI 예진", callback_data="mode_triage")],
        [InlineKeyboardButton("🍎 생활습관 도우미", callback_data="mode_lifestyle")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✈️ **A.F. MEDI+ 비대면 진료/건강관리 봇**\n\n"
        "원하는 서비스를 선택하세요.\n"
        "• AI 예진: 증상을 말씀하시면 분류 후 예약을 도와드립니다.\n"
        "• 생활습관 도우미: 건강검진 결과 조회, 식이/운동 상담",
        reply_markup=reply_markup
    )

async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = get_session(user_id)
    data = query.data

    if data == "mode_triage":
        session["mode"] = "triage"
        session["history"] = []
        session["triage_done"] = False
        await query.edit_message_text("🩺 **AI 예진 모드**\n\n증상과 함께 군번, 계급, 이름을 알려주세요.\n예: `25-12345678 병장 김민수, 어제부터 목이 아프고 열이 37.8도 나요.`")
    elif data == "mode_lifestyle":
        session["mode"] = "lifestyle"
        session["history"] = []
        await query.edit_message_text("🍎 **생활습관 도우미 모드**\n\n무엇이든 물어보세요.\n- '내 건강검진 결과 보여줘'\n- '감기 빨리 낫는 법'\n- '단백질 식단 추천'\n\n검진 결과를 조회하려면 군번을 알려주셔야 합니다.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    text = update.message.text.strip()

    if session["mode"] == "triage" and not session["triage_done"]:
        await handle_triage_message(update, context, session, text)
    elif session["mode"] == "lifestyle":
        await handle_lifestyle_message(update, context, session, text)
    else:
        await update.message.reply_text("먼저 /start 를 눌러 모드를 선택해주세요.")

async def handle_triage_message(update, context, session, user_text):
    session["history"].append({"role": "user", "parts": [user_text]})
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        ai_response = generate_with_gemini(TRIAGE_SYSTEM_PROMPT, session["history"])
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
                f"📋 **AI 예진 결과 (Level 1)**\n\n{desc}\n\n💡 {rec}\n\n의무병 전화상담 예약 가능 시간입니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif level == 2:
            keyboard = [[InlineKeyboardButton(f"{t}", callback_data=f"book_doctor_{t}")] for t in DOCTOR_SLOTS]
            keyboard.append([InlineKeyboardButton("취소", callback_data="cancel_booking")])
            await update.message.reply_text(
                f"📋 **AI 예진 결과 (Level 2)**\n\n{desc}\n\n💡 {rec}\n\n군의관 원격 진료 가능 시간입니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif level == 3:
            await update.message.reply_text(
                f"🚨 **응급 상황 (Level 3)**\n\n{desc}\n\n{rec}\n\n⚠️ 즉시 응급실로 이동하십시오. 부대 상황병에게도 자동 전파되었습니다."
            )
            session["mode"] = None
        else:
            await update.message.reply_text("분류 오류가 발생했습니다.")
            session["mode"] = None
    else:
        await update.message.reply_text(ai_response)

async def handle_lifestyle_message(update, context, session, user_text):
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
        data_str = f"\n\n[현재 조회 중인 병사 정보]\n군번: {snum}\n이름: {soldier_data['이름']} {soldier_data['계급']}\n검진일: {soldier_data['검진일']}\n"
        for k, v in soldier_data["결과"].items():
            data_str += f"- {k}: {v}\n"
        enriched_prompt += data_str

    history = session.get("history", [])
    history.append({"role": "user", "parts": [user_text]})

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        ai_response = generate_with_gemini(enriched_prompt, history)
    except Exception as e:
        await update.message.reply_text(f"🚨 시스템 오류: {str(e)[:200]}")
        return

    history.append({"role": "model", "parts": [ai_response]})
    session["history"] = history
    await update.message.reply_text(ai_response)

async def booking_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    session = get_session(user_id)

    if data == "cancel_booking":
        session["mode"] = None
        await query.edit_message_text("예약이 취소되었습니다. /start 로 돌아가세요.")
        return

    if data.startswith("book_medic_"):
        time = data.replace("book_medic_", "")
        await query.edit_message_text(
            f"✅ **의무병 전화상담 예약 완료**\n\n• 예약 시간: {time}\n• 상담 내용: Level 1 경증 진료\n\n📞 실제 서비스에서는 자동 안내가 발송됩니다."
        )
    elif data.startswith("book_doctor_"):
        time = data.replace("book_doctor_", "")
        await query.edit_message_text(
            f"✅ **군의관 원격 진료 예약 완료**\n\n• 예약 시간: {time}\n• 진료 과목: 내과/일반\n\n보안이 확보된 국방망 단말기로 접속해 주십시오."
        )
    session["mode"] = None

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set.")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mode_selection, pattern="^mode_"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^(book_|cancel_booking)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✈️ MEDI+ 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
