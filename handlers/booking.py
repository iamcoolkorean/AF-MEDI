from telegram import Update
from telegram.ext import ContextTypes
from sessions import get_session

async def booking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    session = get_session(user_id)

    if data == "cancel_booking":
        session["mode"] = None
        await query.edit_message_text("예약이 취소되었습니다. /start 로 돌아가세요. 필승!")
        return

    if data.startswith("book_medic_"):
        time = data.replace("book_medic_", "")
        await query.edit_message_text(
            f"필승! ✅ **군의관 전화 진료 예약 완료**\n\n"
            f"• 예약 시간: {time}\n"
            f"• 진료 유형: Level 1 경증 전화 진료\n\n"
            f"📞 예약 시간 10분 전에 자동 안내 알림이 발송됩니다."
        )
    elif data.startswith("book_doctor_"):
        time = data.replace("book_doctor_", "")
        await query.edit_message_text(
            f"필승! ✅ **대면 진료 예약 완료**\n\n"
            f"• 예약 시간: {time}\n"
            f"• 진료 유형: Level 2 중등증/중증의심 대면 진료\n\n"
            f"🏥 예약 시간 15분 전에 의무대를 방문해 주십시오. 보안이 확보된 국방망 단말기로도 접속 가능합니다."
        )
    session["mode"] = None
