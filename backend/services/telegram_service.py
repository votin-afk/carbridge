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
    message_preview: str,
    deal_id: str = None,
    stage_key: str = None
) -> bool:
    """Notify user about new message in deal chat with reply button"""
    text = f"""
💬 <b>Новое сообщение</b>

От: {sender_name}
Авто: {car_name}
Этап: {stage_name}

<i>{message_preview[:200]}{'...' if len(message_preview) > 200 else ''}</i>

<i>Ответьте на это сообщение, чтобы отправить ответ в чат.</i>
"""
    # Add reply button if deal_id and stage_key provided
    reply_markup = None
    if deal_id and stage_key:
        reply_markup = {
            "inline_keyboard": [[
                {
                    "text": "💬 Ответить",
                    "callback_data": f"reply:{deal_id}:{stage_key}"
                }
            ]]
        }
    
    return await send_telegram_message(chat_id, text, reply_markup=reply_markup)


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



async def send_chat_selection(
    chat_id: int,
    active_chats: List[Dict],
    prompt_text: str = "Выберите чат для отправки сообщения:"
) -> bool:
    """Send inline keyboard with active chat selection"""
    text = f"""
📋 <b>{prompt_text}</b>

У вас несколько активных чатов. Выберите, куда отправить сообщение:
"""
    
    # Build inline keyboard with chat options
    keyboard = []
    for chat in active_chats[:8]:  # Limit to 8 chats
        car_name = chat.get('car_name', 'Авто')
        stage_label = STAGE_LABELS.get(chat.get('stage_key', ''), chat.get('stage_key', ''))
        deal_id = chat.get('deal_id', '')
        stage_key = chat.get('stage_key', '')
        
        keyboard.append([{
            "text": f"🚗 {car_name} - {stage_label}",
            "callback_data": f"select:{deal_id}:{stage_key}"
        }])
    
    reply_markup = {"inline_keyboard": keyboard}
    return await send_telegram_message(chat_id, text, reply_markup=reply_markup)


async def send_message_confirmation(
    chat_id: int,
    car_name: str,
    stage_key: str
) -> bool:
    """Send confirmation that message was delivered to chat"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    text = f"""
✅ <b>Сообщение отправлено</b>

Ваше сообщение доставлено в чат:
🚗 {car_name}
📋 Этап: {stage_label}
"""
    return await send_telegram_message(chat_id, text)


async def send_awaiting_message_prompt(
    chat_id: int,
    car_name: str,
    stage_key: str
) -> bool:
    """Prompt user to send their message for the selected chat"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    text = f"""
📝 <b>Выбран чат:</b>

🚗 {car_name}
📋 Этап: {stage_label}

Напишите ваше сообщение, и оно будет отправлено в этот чат.
Или нажмите /cancel для отмены.
"""
    return await send_telegram_message(chat_id, text)


async def send_no_active_chats(chat_id: int) -> bool:
    """Inform user they have no active chats"""
    text = """
❌ <b>Нет активных чатов</b>

У вас пока нет активных сделок с чатами.

Чтобы начать общение:
1. Создайте сделку на сайте
2. Выберите подрядчика для этапа
3. После этого чат станет доступен
"""
    return await send_telegram_message(chat_id, text)


async def send_error_message(chat_id: int, error_text: str) -> bool:
    """Send error message to user"""
    text = f"""
⚠️ <b>Ошибка</b>

{error_text}

Попробуйте ещё раз или обратитесь в поддержку.
"""
    return await send_telegram_message(chat_id, text)



# ==================== MODERATOR NOTIFICATIONS ====================

async def notify_moderators_new_user(
    moderator_chat_ids: List[int],
    user_name: str,
    user_email: str,
    user_phone: str,
    user_type: str = "user"
) -> int:
    """Notify all moderators about new user registration"""
    type_label = "Пользователь" if user_type == "user" else "Подрядчик"
    text = f"""
👤 <b>Новая регистрация</b>

Тип: {type_label}
Имя: {user_name}
Email: {user_email}
Телефон: {user_phone}

Проверьте в панели модератора.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_stage_review(
    moderator_chat_ids: List[int],
    client_name: str,
    car_name: str,
    stage_key: str,
    contractor_name: str,
    deal_id: str
) -> int:
    """Notify moderators about stage pending review"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    text = f"""
🔍 <b>Этап на проверке</b>

Клиент: {client_name}
Авто: {car_name}
Этап: {stage_label}
Подрядчик: {contractor_name}

Требуется проверка и одобрение.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_verification_request(
    moderator_chat_ids: List[int],
    user_name: str,
    user_email: str,
    user_phone: str
) -> int:
    """Notify moderators about user verification request"""
    text = f"""
📋 <b>Запрос верификации</b>

Пользователь: {user_name}
Email: {user_email}
Телефон: {user_phone}

Проверьте документы и подтвердите верификацию.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_prepayment_request(
    moderator_chat_ids: List[int],
    user_name: str,
    user_email: str,
    amount: float
) -> int:
    """Notify moderators about prepayment confirmation request"""
    text = f"""
💰 <b>Запрос подтверждения предоплаты</b>

Пользователь: {user_name}
Email: {user_email}
Сумма: ${amount}

Проверьте оплату и подтвердите.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_contractor_approval(
    moderator_chat_ids: List[int],
    company_name: str,
    contractor_type: str,
    email: str,
    services: str
) -> int:
    """Notify moderators about new contractor pending approval"""
    text = f"""
🏢 <b>Новый подрядчик ожидает одобрения</b>

Компания: {company_name}
Тип: {contractor_type}
Email: {email}
Услуги: {services}

Проверьте и одобрите в панели модератора.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_contractor_assignment(
    moderator_chat_ids: List[int],
    client_name: str,
    car_name: str,
    stage_key: str,
    contractor_name: str,
    price: float
) -> int:
    """Notify moderators about contractor assignment awaiting approval"""
    stage_label = STAGE_LABELS.get(stage_key, stage_key)
    text = f"""
📝 <b>Назначение подрядчика</b>

Клиент: {client_name}
Авто: {car_name}
Этап: {stage_label}
Подрядчик: {contractor_name}
Стоимость: ${price}

Требуется одобрение назначения.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_new_tender(
    moderator_chat_ids: List[int],
    client_name: str,
    car_brand: str,
    car_model: str,
    budget: str
) -> int:
    """Notify moderators about new tender created"""
    text = f"""
📢 <b>Новый тендер</b>

Клиент: {client_name}
Авто: {car_brand} {car_model}
Бюджет: {budget}

Новый тендер создан в системе.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_new_application(
    moderator_chat_ids: List[int],
    client_name: str,
    car_brand: str,
    car_model: str,
    budget: str
) -> int:
    """Notify moderators about new application"""
    text = f"""
📄 <b>Новая заявка на подбор</b>

Клиент: {client_name}
Авто: {car_brand} {car_model}
Бюджет: {budget}

Новая заявка на подбор автомобиля.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count


async def notify_moderators_manager_help_request(
    moderator_chat_ids: List[int],
    client_name: str,
    client_email: str,
    client_phone: str,
    car_info: str
) -> int:
    """Notify moderators about manager help request"""
    text = f"""
🆘 <b>Запрос помощи менеджера</b>

Клиент: {client_name}
Email: {client_email}
Телефон: {client_phone}
Авто: {car_info}

Клиент запросил помощь менеджера ($200).
Свяжитесь с клиентом.
"""
    success_count = 0
    for chat_id in moderator_chat_ids:
        if await send_telegram_message(chat_id, text):
            success_count += 1
    return success_count
