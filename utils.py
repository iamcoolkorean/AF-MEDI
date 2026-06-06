from telegram import Update
from telegram.ext import ContextTypes

def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """긴 텍스트를 텔레그램 메시지 길이 제한에 맞게 분할한다."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    while len(text) > max_length:
        # 최대 길이에서 마지막 줄바꿈 위치를 찾아 자연스럽게 자름
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
