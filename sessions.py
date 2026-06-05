from typing import Dict

user_sessions: Dict[int, dict] = {}

def get_session(user_id: int) -> dict:
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "mode": None,          # "triage" or "lifestyle"
            "history": [],         # 대화 기록
            "soldier_id": None,    # 조회 중인 군번
            "triage_done": False   # 예진 최종 분류 완료 여부
        }
    return user_sessions[user_id]
