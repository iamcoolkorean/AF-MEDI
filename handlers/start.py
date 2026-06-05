from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sessions import get_session

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
