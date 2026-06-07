from telegram import Update
from telegram.ext import ContextTypes
from google import genai
from google.genai import types
from config import get_next_api_key
from typing import List

# 오늘의 급식 목업 데이터 (수정 없음)
MOCK_MEAL_MENU = {
    "아침": "현미밥, 북어국, 계란말이, 김치",
    "점심": "보리밥, 닭가슴살 샐러드, 된장국, 배추김치",
    "저녁": "잡곡밥, 미역국, 제육볶음, 깍두기, 두부부침"
}

# ... (soldier_data_to_text, split_long_message, send_long_message 함수는 이전과 동일) ...

async def generate_preliminary_chart(soldier_name: str, history: List[dict]) -> str:
    """
    대화 기록을 분석하여 군의관 차팅용 예비 문진표를 생성한다.
    주요 증상을 키워드 형태로 추출하여 포함시킨다.
    """
    if not history:
        return "예비 문진표를 생성할 대화 기록이 없습니다."

    # 1. 증상 추출을 위한 프롬프트 준비
    extraction_prompt = """
    너는 의무대 AI 어시스턴트야. 다음 환자-AI 대화를 분석하여 주요 증상을 단일 키워드 또는 짧은 구문으로 추출해줘.
    예시: 마른기침, 미열(37.8℃), 두통, 인후통, 콧물
    증상만 쉼표로 구분해서 나열하고, 다른 설명은 하지 마.
    """

    # 최근 10개의 메시지를 텍스트로 변환
    recent_history = history[-10:]
    chat_text = ""
    for msg in recent_history:
        role = "환자" if msg["role"] == "user" else "AI"
        chat_text += f"[{role}]: {msg['parts'][0]}\n"

    # 2. Gemini API 호출하여 증상 추출
    key = get_next_api_key()
    if not key:
        return "API 키가 설정되지 않았습니다."

    client = genai.Client(api_key=key)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=chat_text)])],
            config=types.GenerateContentConfig(
                system_instruction=extraction_prompt,
                temperature=0.3,  # 일관된 결과를 위해 낮게 설정
                max_output_tokens=256
            )
        )
        symptoms = response.text.strip()
    except Exception:
        # 호출 실패 시 기본 메시지
        symptoms = "증상 추출 실패 (수동 확인 필요)"

    # 3. 최종 문진표 생성
    chart = f"""
📋 **예비 문진표 - {soldier_name}**

**주요 증상:** {symptoms}

**대화 요약:**
{chat_text}

**과거 병력:**
건강검진 데이터 기반으로 의무대에서 확인 필요.

**초진 소견 (AI 분류):**
환자-AI 대화 기반으로 자동 분류된 예비 소견입니다. 군의관 최종 확인 바랍니다.

---
*본 문진표는 AI 예진 챗봇이 자동 생성한 자료입니다.*
"""
    return chart
