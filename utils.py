from telegram import Update
from telegram.ext import ContextTypes

# 오늘의 급식 목업 데이터
MOCK_MEAL_MENU = {
    "아침": "현미밥, 북어국, 계란말이, 김치",
    "점심": "보리밥, 닭가슴살 샐러드, 된장국, 배추김치",
    "저녁": "잡곡밥, 미역국, 제육볶음, 깍두기, 두부부침"
}

def soldier_data_to_text(snum: str, data: dict) -> str:
    """병사 검진 데이터를 AI에게 전달할 텍스트로 변환"""
    text = f"\n\n[현재 조회 중인 병사 정보]\n군번: {snum}\n이름: {data['이름']} {data['계급']}\n검진일: {data['검진일']}\n"
    for k, v in data["결과"].items():
        text += f"- {k}: {v}\n"
    return text

def generate_preliminary_chart(soldier_name: str, history: list) -> str:
    """대화 기록을 바탕으로 군의관 차팅용 예비 문진표를 생성한다."""
    if not history:
        return "예비 문진표를 생성할 대화 기록이 없습니다."

    # 마지막 6개의 대화(사용자 3번, AI 3번)를 기반으로 문진표 작성
    chat_summary = ""
    for msg in history[-6:]:
        role = "병사" if msg["role"] == "user" else "AI"
        chat_summary += f"[{role}]: {msg['parts'][0]}\n"

    chart = f"""
📋 **[예비 문진표 - {soldier_name}]**

1. **주요 호소 증상 및 현 병력**
{chat_summary}

2. **과거 병력**
건강검진 데이터 기반으로 의무대에서 확인 필요.

3. **초진 소견 (AI 분류)**
상기 환자는 챗봇 자가진단을 통해 Level 1(경증) 또는 Level 2(중등증)로 분류되었습니다. 
군의관 확인 후 최종 진료 바랍니다.

* 본 문진표는 AI가 대화를 통해 자동 생성한 예비 자료입니다.
"""
    return chart

def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """긴 텍스트를 텔레그램 메시지 길이 제한에 맞게 분할한다."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    while len(text) > max_length:
        split_point = text.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        chunks.append(text[:split_point])
        text = text[split_point:].lstrip('\n')
    if text:
        chunks.append(text)
    return chunks

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """긴 메시지를 분할하여 순차적으로 전송한다."""
    chunks = split_long_message(text)
    for chunk in chunks:
        await update.message.reply_text(chunk)
