import logging

from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

DECLINE_PROMPT = (
    "あなたは大学の教授です。学生から単位を個別に融通してほしいという"
    "お願いのメッセージが届きました。丁寧だが毅然と断る返信メッセージを"
    "日本語で3文以内、本文のみで書いてください。"
)

DUMMY_DECLINE_MESSAGE = (
    "ご相談ありがとうございます。しかし成績評価は公正な基準に基づいて行っており、"
    "個別の単位付与のご依頼にはお応えできません。ご了承ください。"
)


def get_gemini_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_decline_reply():
    if not settings.GEMINI_API_KEY:
        return DUMMY_DECLINE_MESSAGE

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=DECLINE_PROMPT,
        )
        text = (response.text or "").strip()
        
        return text or DUMMY_DECLINE_MESSAGE
    
    except Exception:
        logger.exception("Gemini API call failed, falling back to dummy decline message")
        return DUMMY_DECLINE_MESSAGE
