import google.generativeai as genai
from config import get_next_api_key
from typing import List

def generate_response(system_prompt: str, history: List[dict], model_name: str = "gemini-1.5-flash") -> str:
    """Gemini API를 호출하고 응답 텍스트를 반환한다."""
    key = get_next_api_key()
    if not key:
        return "API 키가 설정되지 않았습니다."

    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)

    # 히스토리를 Gemini 형식으로 변환
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [msg["parts"][0]]})

    response = model.generate_content(contents)
    return response.text
