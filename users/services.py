import logging
import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def send_telegram_verification_code(username: str, code: str, expires_in_minutes: int = 15) -> bool:
    if not username:
        return False

    url = getattr(settings, 'TG_BOT_API_URL', '')
    api_key = getattr(settings, 'TG_BOT_API_KEY', '')

    # Форматируем дату в ISO 8601 с часовым поясом (например, "2026-10-02T15:30:00Z")
    expires_at = (timezone.now() + timedelta(minutes=expires_in_minutes)).strftime('%Y-%m-%dT%H:%M:%SZ')

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }

    payload = {
        'username': username.lstrip('@'),  # Убираем @, если пользователь ввел его
        'code': str(code),
        'expires_at': expires_at
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Ошибка отправки кода в Telegram API: {e}")
        return False
