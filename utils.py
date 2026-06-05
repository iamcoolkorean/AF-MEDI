def soldier_data_to_text(snum: str, data: dict) -> str:
    """병사 검진 데이터를 AI에게 전달할 텍스트로 변환"""
    text = f"\n\n[현재 조회 중인 병사 정보]\n군번: {snum}\n이름: {data['이름']} {data['계급']}\n검진일: {data['검진일']}\n"
    for k, v in data["결과"].items():
        text += f"- {k}: {v}\n"
    return text
