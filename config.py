import os
import threading

# 텔레그램 봇 토큰 (환경변수 TELEGRAM_BOT_TOKEN)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Gemini API 키 8개 (GEMINI_API_KEY_1 ~ GEMINI_API_KEY_8)
GEMINI_API_KEYS = []
for i in range(1, 9):
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if key:
        GEMINI_API_KEYS.append(key)

if not GEMINI_API_KEYS:
    print("⚠️ WARNING: No Gemini API keys found. Bot will not work.")

_key_lock = threading.Lock()
_current_idx = 0

def get_next_api_key() -> str:
    global _current_idx
    with _key_lock:
        if not GEMINI_API_KEYS:
            return ""
        key = GEMINI_API_KEYS[_current_idx]
        _current_idx = (_current_idx + 1) % len(GEMINI_API_KEYS)
        return key

# 예약 시간표
MEDIC_PHONE_SLOTS = ["10:00", "11:00", "13:30", "14:30", "16:00"]
DOCTOR_SLOTS = ["09:30", "10:30", "14:00", "15:00", "16:00"]
