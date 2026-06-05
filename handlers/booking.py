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
