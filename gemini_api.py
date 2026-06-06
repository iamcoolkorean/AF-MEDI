from google import genai
from config import get_next_api_key
from typing import List

def generate_response(system_prompt: str, history: List[dict], model_name: str = "gemini-1.5-flash") -> str:
    """Gemini API를 호출하고 응답 텍스트를 반환한다. (google-genai 패키지 사용)"""
    key = get_next_api_key()
    if not key:
        return "API 키가 설정되지 않았습니다."

    # 새 클라이언트 생성
    client = genai.Client(api_key=key)

    # 히스토리를 Gemini 호환 Contents 형식으로 변환
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["parts"][0]}]})

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=1024,
            )
        )
        return response.text
    except Exception as e:
        return f"🚨 AI 호출 중 오류가 발생했습니다: {str(e)[:200]}"
