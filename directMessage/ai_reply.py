import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from google import genai

from .models import Conversation

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

DECLINE_PROMPT = (
    "あなたは大学の教授です。学生から以下のお願いのメッセージが届きました。丁寧だが毅然と断る返信メッセージを日本語で3文以内、本文のみで書いてください。"
)

DUMMY_DECLINE_MESSAGE = (
    "ご相談ありがとうございます。しかし成績評価は公正な基準に基づいて行っており、"
    "個別の単位付与のご依頼にはお応えできません。ご了承ください。"
)


def get_gemini_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_decline_reply(conversation_id):
    if not settings.GEMINI_API_KEY:
        return DUMMY_DECLINE_MESSAGE

    conversation = get_object_or_404(Conversation, pk=conversation_id)
    messages = list(conversation.messages.select_related('sender'))

    last_own_index = -1
    for i, m in enumerate(messages):
        if m.sender_id == conversation.professor_id:
            last_own_index = i

    # 最後に送信した自分のメッセージ以降の学生からのメッセージを取得
    pending = []
    for m in messages[last_own_index + 1:]:
        if m.sender_id != conversation.professor_id:
            pending.append(m.body)

    if not pending:
        return DUMMY_DECLINE_MESSAGE

    student_recent_message = "\n".join(pending)

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=DECLINE_PROMPT + "\n\n学生からのメッセージ:\n" + student_recent_message,
        )
        text = (response.text or "").strip()

        return text or DUMMY_DECLINE_MESSAGE

    except Exception:
        logger.exception("Gemini API call failed, falling back to dummy decline message")
        return DUMMY_DECLINE_MESSAGE
