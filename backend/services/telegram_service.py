"""
Telegram Notification Service
Handles sending notifications and two-way messaging via Telegram bot
"""
import os
import httpx
import asyncio
import json
from typing import Optional, List, Dict
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Stage labels for notifications
STAGE_LABELS = {
    "leasing": "Лизинг",
    "inspection": "Инспекция",
    "export": "Выкуп",
    "logistics_china": "Доставка (Китай)",
    "insurance": "Страхование",
    "delivery_rb": "Доставка (РБ)",
    "customs": "Таможня",
    "completion": "Завершение"
}


async def send_telegram_message(
    chat_id: int, 
    text: str, 
    parse_mode: str = "HTML",
    reply_markup: Optional[dict] = None
) -> bool:
    """Send a message via Telegram bot with optional inline keyboard"""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json=payload,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


async def answer_callback_query(callback_query_id: str, text: str = "") -> bool:
    """Answer a callback query from inline keyboard"""
    if not TELEGRAM_BOT_TOKEN:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_query_id,
                    "text": text
                },
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Telegram callback answer error: {e}")
        return False


async def edit_message_text(
    chat_id: int,
    message_id: int,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: Optional[dict] = None
) -> bool:
    """Edit an existing message"""
    if not TELEGRAM_BOT_TOKEN:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(
                f"{TELEGRAM_API_URL}/editMessageText",
                json=payload,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Telegram edit message error: {e}")
        return False


async def get_bot_info() -> dict:
    """Get bot info to verify token"""
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "error": "No token"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TELEGRAM_API_URL}/getMe", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def notify_new_message(
    chat_id: int,
    sender_name: str,
    car_name: str,
    stage_name: str,
    message_preview: str
) -> bool:
    """Notify user about new message in deal chat"""
    text = f"""
💬 <b>Новое сообщение</b>

От: {sender_name}
Авто: {car_name}
Этап: {stage_name}

<i>{message_preview[:200]}{'...' if len(message_preview) > 200 else ''}</i>
"""
    return await send_telegram_message(chat_id, text)


async def notify_stage_status_change(
    chat_id: int,
    car_name: str,
    stage_key: str,
    new_status: str,
    contractor_name: Optional[str] = None
) -> bool:
    """Notify user about stage status change"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    
    status_emoji = {
        "approved": "✅",
        "completed": "🎉",
        "paid": "💰",
        "pending_review": "🔍",
        "awaiting_approval": "⏳"
    }.get(new_status, "📋")
    
    status_text = {
        "approved": "Подтверждён модератором",
        "completed": "Завершён",
        "paid": "Оплачен",
        "pending_review": "На проверке у модератора",
        "awaiting_approval": "Ожидает подтверждения"
    }.get(new_status, new_status)
    
    text = f"""
{status_emoji} <b>Изменение статуса этапа</b>

Авто: {car_name}
Этап: {stage_label}
Статус: {status_text}
"""
    if contractor_name:
        text += f"Подрядчик: {contractor_name}\n"
    
    return await send_telegram_message(chat_id, text)


async def notify_moderator_action(
    chat_id: int,
    car_name: str,
    stage_key: str,
    action: str,
    moderator_comment: Optional[str] = None
) -> bool:
    """Notify user about moderator action"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    
    if action == "approved":
        text = f"""
✅ <b>Этап одобрен модератором</b>

Авто: {car_name}
Этап: {stage_label}

Теперь вы можете оплатить этот этап.
"""
    elif action == "rejected":
        text = f"""
❌ <b>Этап отклонён модератором</b>

Авто: {car_name}
Этап: {stage_label}
"""
        if moderator_comment:
            text += f"\nКомментарий: {moderator_comment}"
    else:
        text = f"""
📋 <b>Действие модератора</b>

Авто: {car_name}
Этап: {stage_label}
Действие: {action}
"""
    
    return await send_telegram_message(chat_id, text)


async def notify_new_tender(
    chat_id: int,
    car_brand: str,
    car_model: str,
    budget_from: Optional[int],
    budget_to: Optional[int],
    stages: list
) -> bool:
    """Notify contractor about new tender"""
    stages_text = ", ".join([STAGE_LABELS.get(s, s) for s in stages]) if stages else "Все этапы"
    budget_text = ""
    if budget_from and budget_to:
        budget_text = f"Бюджет: ${budget_from:,} - ${budget_to:,}"
    elif budget_from:
        budget_text = f"Бюджет: от ${budget_from:,}"
    elif budget_to:
        budget_text = f"Бюджет: до ${budget_to:,}"
    
    text = f"""
🔔 <b>Новый тендер!</b>

Авто: {car_brand} {car_model}
{budget_text}
Этапы: {stages_text}

Зайдите в личный кабинет, чтобы сделать предложение.
"""
    return await send_telegram_message(chat_id, text)


async def notify_tender_offer_accepted(
    chat_id: int,
    car_name: str,
    stages: list,
    client_name: str
) -> bool:
    """Notify contractor that their tender offer was accepted"""
    stages_text = ", ".join([STAGE_LABELS.get(s, s) for s in stages])
    
    text = f"""
🎉 <b>Ваше предложение принято!</b>

Авто: {car_name}
Клиент: {client_name}
Этапы: {stages_text}

Ожидайте подтверждения модератора для начала работы.
"""
    return await send_telegram_message(chat_id, text)


async def notify_contractor_assigned(
    chat_id: int,
    car_name: str,
    stage_key: str,
    client_name: str
) -> bool:
    """Notify contractor that they were assigned to a stage"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    
    text = f"""
📋 <b>Вы назначены на этап</b>

Авто: {car_name}
Этап: {stage_label}
Клиент: {client_name}

Ожидайте подтверждения модератора.
"""
    return await send_telegram_message(chat_id, text)


async def send_verification_code(chat_id: int, code: str) -> bool:
    """Send verification code for Telegram account linking"""
    text = f"""
🔐 <b>Код подтверждения</b>

Ваш код для привязки Telegram: <code>{code}</code>

Введите этот код в личном кабинете на сайте.
"""
    return await send_telegram_message(chat_id, text)


async def send_welcome_message(chat_id: int, user_name: str) -> bool:
    """Send welcome message when user links their Telegram"""
    text = f"""
👋 <b>Добро пожаловать, {user_name}!</b>

Ваш Telegram успешно привязан к аккаунту.

Теперь вы будете получать уведомления о:
• Новых сообщениях в чатах сделок
• Изменениях статуса этапов
• Действиях модератора
• Новых тендерах (для подрядчиков)

Чтобы отписаться от уведомлений, измените настройки в личном кабинете.
"""
    return await send_telegram_message(chat_id, text)
