from google import genai
from google.genai import types
from config import get_next_api_key
from typing import List

MODEL_NAME = "gemini-2.5-flash"

def generate_response(system_prompt: str, history: List[dict]) -> str:
    key = get_next_api_key()
    if not key:
        return "API 키가 설정되지 않았습니다."

    client = genai.Client(api_key=key)

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg["parts"][0])]
        ))

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=4096,   # ← 길이 확보
            )
        )
        return response.text
    except Exception as e:
        return f"🚨 AI 호출 중 오류: {str(e)[:200]}"
