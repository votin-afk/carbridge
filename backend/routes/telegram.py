"""Telegram integration routes - webhook, linking, notifications"""
from fastapi import APIRouter, HTTPException, Depends, Request
import os
import uuid
import random
import string
import logging
from datetime import datetime, timezone
import httpx

import sys
sys.path.insert(0, '/app/backend')

from database import db
from config import UPLOADS_DIR
from utils.auth import get_current_user, get_current_contractor, require_role
from services import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])

# Store pending telegram verifications (in production, use Redis or DB)
telegram_pending_verifications = {}

# Store pending message context for two-way messaging
# Format: {chat_id: {"deal_id": ..., "stage_key": ..., "user_id": ..., "user_type": ...}}
telegram_message_context = {}


# ==================== HELPER FUNCTIONS ====================

async def get_moderator_chat_ids() -> list:
    """Get list of Telegram chat_ids for all moderators and admins"""
    moderators = await db.users.find(
        {
            "role": {"$in": ["moderator", "admin"]},
            "telegram_chat_id": {"$exists": True, "$ne": None}
        },
        {"_id": 0, "telegram_chat_id": 1}
    ).to_list(50)
    return [m["telegram_chat_id"] for m in moderators]


async def get_user_active_chats(user_id: str, user_type: str = "user"):
    """Get list of active chats for user/contractor"""
    active_chats = []
    
    if user_type == "user":
        deals = await db.deals.find({"user_id": user_id}).to_list(50)
        for deal in deals:
            car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
            stages = deal.get("stages", {})
            if isinstance(stages, dict):
                for stage_key, stage_data in stages.items():
                    if stage_data.get("contractor_id"):
                        active_chats.append({
                            "deal_id": deal["id"],
                            "stage_key": stage_key,
                            "car_name": car_name.strip() or "Авто",
                            "contractor_name": stage_data.get("contractor_name", "")
                        })
    else:
        deals = await db.deals.find({}).to_list(100)
        for deal in deals:
            car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
            stages = deal.get("stages", {})
            if isinstance(stages, dict):
                for stage_key, stage_data in stages.items():
                    if stage_data.get("contractor_id") == user_id:
                        active_chats.append({
                            "deal_id": deal["id"],
                            "stage_key": stage_key,
                            "car_name": car_name.strip() or "Авто",
                            "client_id": deal.get("user_id")
                        })
    
    return active_chats


async def send_message_to_deal_chat(
    deal_id: str,
    stage_key: str,
    sender_id: str,
    sender_type: str,
    sender_name: str,
    content: str,
    file_ids: list = None
):
    """Send a message to deal stage chat from Telegram"""
    message_doc = {
        "id": str(uuid.uuid4()),
        "deal_id": deal_id,
        "stage_key": stage_key,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_type": sender_type,
        "content": content,
        "file_ids": file_ids or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by_client": sender_type == "client",
        "read_by_contractor": sender_type == "contractor",
        "source": "telegram"
    }
    await db.deal_messages.insert_one(message_doc)
    return message_doc


async def download_telegram_file(file_id: str) -> tuple:
    """Download a file from Telegram servers. Returns (file_bytes, file_name, mime_type)"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return None, None, None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": file_id},
                timeout=15.0
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"Telegram getFile failed: {data}")
                return None, None, None
            
            file_path = data["result"]["file_path"]
            file_name = file_path.split("/")[-1] if "/" in file_path else file_path
            
            file_resp = await client.get(
                f"https://api.telegram.org/file/bot{bot_token}/{file_path}",
                timeout=30.0
            )
            if file_resp.status_code != 200:
                logger.error(f"Telegram file download failed: {file_resp.status_code}")
                return None, None, None
            
            ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            mime_map = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "gif": "image/gif", "webp": "image/webp", "mp4": "video/mp4",
                "pdf": "application/pdf", "doc": "application/msword",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xls": "application/vnd.ms-excel", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "ogg": "audio/ogg", "mp3": "audio/mpeg", "wav": "audio/wav"
            }
            mime_type = mime_map.get(ext, "application/octet-stream")
            
            return file_resp.content, file_name, mime_type
    except Exception as e:
        logger.error(f"Telegram file download error: {e}")
        return None, None, None


async def save_telegram_file_to_deal(
    deal_id: str,
    stage_key: str,
    sender_id: str,
    sender_name: str,
    sender_type: str,
    file_bytes: bytes,
    file_name: str,
    mime_type: str
) -> str:
    """Save a file downloaded from Telegram to the deal's file storage"""
    file_id = str(uuid.uuid4())
    ext = file_name.rsplit(".", 1)[-1] if "." in file_name else ""
    saved_name = f"{file_id}.{ext}" if ext else file_id
    
    category = "document"
    if mime_type.startswith("image/"):
        category = "photo"
    elif mime_type.startswith("video/"):
        category = "video"
    elif mime_type.startswith("audio/"):
        category = "audio"
    
    deal_dir = UPLOADS_DIR / deal_id
    deal_dir.mkdir(parents=True, exist_ok=True)
    file_path = deal_dir / saved_name
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    file_doc = {
        "id": file_id,
        "deal_id": deal_id,
        "stage_key": stage_key,
        "original_name": file_name,
        "saved_name": saved_name,
        "mime_type": mime_type,
        "size": len(file_bytes),
        "category": category,
        "description": "",
        "uploader_id": sender_id,
        "uploader_name": sender_name,
        "uploader_type": "client" if sender_type == "client" else "contractor",
        "source": "telegram",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deal_files.insert_one(file_doc)
    return file_id


# ==================== WEBHOOK ====================

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Webhook for Telegram bot updates - handles two-way messaging"""
    try:
        data = await request.json()
        logger.info(f"Telegram webhook received: {data.get('message', {}).get('text', '')[:50] if data.get('message') else 'callback'}")
        
        # Handle callback queries (button presses)
        if data.get("callback_query"):
            callback = data["callback_query"]
            callback_id = callback.get("id")
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            callback_data = callback.get("data", "")
            
            parts = callback_data.split(":")
            action = parts[0] if parts else ""
            
            if action == "reply" and len(parts) >= 3:
                deal_id = parts[1]
                stage_key = parts[2]
                
                user = await db.users.find_one({"telegram_chat_id": chat_id})
                contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                
                if user:
                    user_id = user["id"]
                    user_type = "user"
                    user_name = user.get("name", "Клиент")
                elif contractor:
                    user_id = contractor["id"]
                    user_type = "contractor"
                    user_name = contractor.get("company_name", "Подрядчик")
                else:
                    await telegram_service.answer_callback_query(callback_id, "Аккаунт не привязан")
                    return {"ok": True}
                
                deal = await db.deals.find_one({"id": deal_id})
                car_name = ""
                if deal:
                    car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
                
                telegram_message_context[chat_id] = {
                    "deal_id": deal_id,
                    "stage_key": stage_key,
                    "user_id": user_id,
                    "user_type": user_type,
                    "user_name": user_name,
                    "car_name": car_name.strip() or "Авто"
                }
                
                await telegram_service.answer_callback_query(callback_id, "Напишите ответ")
                await telegram_service.send_awaiting_message_prompt(chat_id, car_name.strip() or "Авто", stage_key)
                
            elif action == "select" and len(parts) >= 3:
                deal_id = parts[1]
                stage_key = parts[2]
                
                user = await db.users.find_one({"telegram_chat_id": chat_id})
                contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                
                if user:
                    user_id = user["id"]
                    user_type = "user"
                    user_name = user.get("name", "Клиент")
                elif contractor:
                    user_id = contractor["id"]
                    user_type = "contractor"
                    user_name = contractor.get("company_name", "Подрядчик")
                else:
                    await telegram_service.answer_callback_query(callback_id, "Аккаунт не привязан")
                    return {"ok": True}
                
                deal = await db.deals.find_one({"id": deal_id})
                car_name = ""
                if deal:
                    car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
                
                telegram_message_context[chat_id] = {
                    "deal_id": deal_id,
                    "stage_key": stage_key,
                    "user_id": user_id,
                    "user_type": user_type,
                    "user_name": user_name,
                    "car_name": car_name.strip() or "Авто"
                }
                
                await telegram_service.answer_callback_query(callback_id, "Чат выбран")
                await telegram_service.send_awaiting_message_prompt(chat_id, car_name.strip() or "Авто", stage_key)
            
            return {"ok": True}
        
        # Handle regular messages
        if data.get("message"):
            message = data["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "") or message.get("caption", "") or ""
            username = message.get("from", {}).get("username")
            first_name = message.get("from", {}).get("first_name", "")
            
            # Detect file attachments
            telegram_file_id = None
            telegram_file_name = None
            if message.get("photo"):
                telegram_file_id = message["photo"][-1]["file_id"]
                telegram_file_name = f"photo_{message['message_id']}.jpg"
            elif message.get("document"):
                telegram_file_id = message["document"]["file_id"]
                telegram_file_name = message["document"].get("file_name", f"file_{message['message_id']}")
            elif message.get("video"):
                telegram_file_id = message["video"]["file_id"]
                telegram_file_name = message["video"].get("file_name", f"video_{message['message_id']}.mp4")
            elif message.get("voice"):
                telegram_file_id = message["voice"]["file_id"]
                telegram_file_name = f"voice_{message['message_id']}.ogg"
            elif message.get("audio"):
                telegram_file_id = message["audio"]["file_id"]
                telegram_file_name = message["audio"].get("file_name", f"audio_{message['message_id']}.mp3")
            
            # Handle commands
            if text.startswith("/start"):
                parts = text.split(" ")
                if len(parts) > 1:
                    verification_code = parts[1]
                    if verification_code in telegram_pending_verifications:
                        user_id = telegram_pending_verifications[verification_code]["user_id"]
                        user_type = telegram_pending_verifications[verification_code]["type"]
                        
                        if user_type == "user":
                            await db.users.update_one(
                                {"id": user_id},
                                {"$set": {"telegram_chat_id": chat_id, "telegram_username": username}}
                            )
                            user = await db.users.find_one({"id": user_id})
                            user_name = user.get("name", first_name) if user else first_name
                        else:
                            await db.contractors.update_one(
                                {"id": user_id},
                                {"$set": {"telegram_chat_id": chat_id, "telegram_username": username}}
                            )
                            contractor = await db.contractors.find_one({"id": user_id})
                            user_name = contractor.get("company_name", first_name) if contractor else first_name
                        
                        del telegram_pending_verifications[verification_code]
                        await telegram_service.send_welcome_message(chat_id, user_name)
                        return {"ok": True}
                
                # AUTO-LINK by username
                auto_linked = False
                if username:
                    normalized_username = username.lstrip('@').lower()
                    
                    existing_user = await db.users.find_one({"telegram_chat_id": chat_id})
                    existing_contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                    
                    if not existing_user and not existing_contractor:
                        user = await db.users.find_one({
                            "$or": [
                                {"telegram": {"$regex": f"^@?{normalized_username}$", "$options": "i"}},
                                {"telegram_username": {"$regex": f"^@?{normalized_username}$", "$options": "i"}}
                            ],
                            "telegram_chat_id": {"$exists": False}
                        })
                        
                        if user:
                            await db.users.update_one(
                                {"id": user["id"]},
                                {"$set": {"telegram_chat_id": chat_id, "telegram_username": username}}
                            )
                            await telegram_service.send_welcome_message(chat_id, user.get("name", first_name))
                            auto_linked = True
                            logger.info(f"Auto-linked user {user.get('email')} to Telegram chat {chat_id}")
                        else:
                            contractor = await db.contractors.find_one({
                                "$or": [
                                    {"telegram": {"$regex": f"^@?{normalized_username}$", "$options": "i"}},
                                    {"telegram_username": {"$regex": f"^@?{normalized_username}$", "$options": "i"}}
                                ],
                                "telegram_chat_id": {"$exists": False}
                            })
                            
                            if contractor:
                                await db.contractors.update_one(
                                    {"id": contractor["id"]},
                                    {"$set": {"telegram_chat_id": chat_id, "telegram_username": username}}
                                )
                                await telegram_service.send_welcome_message(chat_id, contractor.get("company_name", first_name))
                                auto_linked = True
                                logger.info(f"Auto-linked contractor {contractor.get('email')} to Telegram chat {chat_id}")
                    else:
                        auto_linked = True
                        user_name = existing_user.get("name") if existing_user else existing_contractor.get("company_name", first_name)
                        await telegram_service.send_telegram_message(
                            chat_id,
                            f"С возвращением, {user_name}!\n\n"
                            "Ваш Telegram уже привязан к аккаунту.\n\n"
                            "<b>Команды:</b>\n"
                            "/chats - Показать активные чаты\n"
                            "/help - Справка"
                        )
                
                if not auto_linked:
                    await telegram_service.send_telegram_message(
                        chat_id,
                        f"Привет, {first_name}!\n\n"
                        "Для получения уведомлений привяжите Telegram в личном кабинете на сайте:\n"
                        "Настройки -> Привязать Telegram\n\n"
                        "<b>Команды:</b>\n"
                        "/chats - Показать активные чаты\n"
                        "/help - Справка"
                    )
            
            elif text.startswith("/help"):
                await telegram_service.send_telegram_message(
                    chat_id,
                    "<b>Команды бота:</b>\n\n"
                    "/start - Начать работу с ботом\n"
                    "/chats - Показать активные чаты\n"
                    "/cancel - Отменить выбор чата\n"
                    "/help - Показать справку\n\n"
                    "Вы можете отвечать на уведомления о сообщениях прямо в Telegram."
                )
            
            elif text.startswith("/chats"):
                user = await db.users.find_one({"telegram_chat_id": chat_id})
                contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                
                if user:
                    active_chats = await get_user_active_chats(user["id"], "user")
                elif contractor:
                    active_chats = await get_user_active_chats(contractor["id"], "contractor")
                else:
                    await telegram_service.send_telegram_message(
                        chat_id,
                        "Ваш Telegram не привязан к аккаунту.\n\n"
                        "Привяжите Telegram в личном кабинете на сайте."
                    )
                    return {"ok": True}
                
                if active_chats:
                    await telegram_service.send_chat_selection(chat_id, active_chats)
                else:
                    await telegram_service.send_no_active_chats(chat_id)
            
            elif text.startswith("/cancel"):
                if chat_id in telegram_message_context:
                    del telegram_message_context[chat_id]
                await telegram_service.send_telegram_message(
                    chat_id,
                    "Выбор чата отменён.\n\nИспользуйте /chats для выбора чата."
                )
            
            elif not text.startswith("/") or telegram_file_id:
                has_content = text.strip() or telegram_file_id
                
                if chat_id in telegram_message_context and has_content:
                    ctx = telegram_message_context[chat_id]
                    sender_type_val = "client" if ctx["user_type"] == "user" else "contractor"
                    
                    saved_file_ids = []
                    if telegram_file_id:
                        file_bytes, file_name, mime_type = await download_telegram_file(telegram_file_id)
                        if file_bytes:
                            fid = await save_telegram_file_to_deal(
                                deal_id=ctx["deal_id"],
                                stage_key=ctx["stage_key"],
                                sender_id=ctx["user_id"],
                                sender_name=ctx["user_name"],
                                sender_type=sender_type_val,
                                file_bytes=file_bytes,
                                file_name=telegram_file_name or file_name,
                                mime_type=mime_type
                            )
                            saved_file_ids.append(fid)
                    
                    msg_content = text.strip() if text.strip() else ""
                    if saved_file_ids and not msg_content:
                        msg_content = f"[Файл: {telegram_file_name}]"
                    
                    await send_message_to_deal_chat(
                        deal_id=ctx["deal_id"],
                        stage_key=ctx["stage_key"],
                        sender_id=ctx["user_id"],
                        sender_type=sender_type_val,
                        sender_name=ctx["user_name"],
                        content=msg_content,
                        file_ids=saved_file_ids
                    )
                    
                    await telegram_service.send_message_confirmation(
                        chat_id,
                        ctx["car_name"],
                        ctx["stage_key"]
                    )
                    
                    # Notify other party
                    deal = await db.deals.find_one({"id": ctx["deal_id"]})
                    if deal and ctx["user_type"] == "user":
                        stage_data = deal.get("stages", {}).get(ctx["stage_key"], {})
                        contractor_id = stage_data.get("contractor_id")
                        if contractor_id:
                            contractor = await db.contractors.find_one({"id": contractor_id})
                            if contractor and contractor.get("telegram_chat_id"):
                                await telegram_service.notify_new_message(
                                    contractor["telegram_chat_id"],
                                    ctx["user_name"],
                                    ctx["car_name"],
                                    telegram_service.STAGE_LABELS.get(ctx["stage_key"], ctx["stage_key"]),
                                    text,
                                    ctx["deal_id"],
                                    ctx["stage_key"]
                                )
                    elif deal and ctx["user_type"] == "contractor":
                        client_id = deal.get("user_id")
                        if client_id:
                            client_user = await db.users.find_one({"id": client_id})
                            if client_user and client_user.get("telegram_chat_id"):
                                await telegram_service.notify_new_message(
                                    client_user["telegram_chat_id"],
                                    ctx["user_name"],
                                    ctx["car_name"],
                                    telegram_service.STAGE_LABELS.get(ctx["stage_key"], ctx["stage_key"]),
                                    text,
                                    ctx["deal_id"],
                                    ctx["stage_key"]
                                )
                    
                else:
                    if not has_content:
                        return {"ok": True}
                    
                    user = await db.users.find_one({"telegram_chat_id": chat_id})
                    contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                    
                    if user:
                        active_chats = await get_user_active_chats(user["id"], "user")
                    elif contractor:
                        active_chats = await get_user_active_chats(contractor["id"], "contractor")
                    else:
                        await telegram_service.send_telegram_message(
                            chat_id,
                            "Ваш Telegram не привязан к аккаунту.\n\n"
                            "Привяжите Telegram в личном кабинете на сайте."
                        )
                        return {"ok": True}
                    
                    if active_chats:
                        if len(active_chats) == 1:
                            chat = active_chats[0]
                            user_id = user["id"] if user else contractor["id"]
                            user_type = "user" if user else "contractor"
                            user_name = user.get("name", "Клиент") if user else contractor.get("company_name", "Подрядчик")
                            sender_type_val = "client" if user_type == "user" else "contractor"
                            
                            telegram_message_context[chat_id] = {
                                "deal_id": chat["deal_id"],
                                "stage_key": chat["stage_key"],
                                "user_id": user_id,
                                "user_type": user_type,
                                "user_name": user_name,
                                "car_name": chat["car_name"]
                            }
                            
                            saved_file_ids = []
                            if telegram_file_id:
                                file_bytes, file_name, mime_type = await download_telegram_file(telegram_file_id)
                                if file_bytes:
                                    fid = await save_telegram_file_to_deal(
                                        deal_id=chat["deal_id"],
                                        stage_key=chat["stage_key"],
                                        sender_id=user_id,
                                        sender_name=user_name,
                                        sender_type=sender_type_val,
                                        file_bytes=file_bytes,
                                        file_name=telegram_file_name or file_name,
                                        mime_type=mime_type
                                    )
                                    saved_file_ids.append(fid)
                            
                            msg_content = text.strip() if text.strip() else ""
                            if saved_file_ids and not msg_content:
                                msg_content = f"[Файл: {telegram_file_name}]"
                            
                            await send_message_to_deal_chat(
                                deal_id=chat["deal_id"],
                                stage_key=chat["stage_key"],
                                sender_id=user_id,
                                sender_type=sender_type_val,
                                sender_name=user_name,
                                content=msg_content,
                                file_ids=saved_file_ids
                            )
                            
                            await telegram_service.send_message_confirmation(
                                chat_id,
                                chat["car_name"],
                                chat["stage_key"]
                            )
                        else:
                            await telegram_service.send_chat_selection(
                                chat_id,
                                active_chats,
                                "Выберите чат для отправки сообщения:"
                            )
                    else:
                        await telegram_service.send_no_active_chats(chat_id)
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"ok": False}


# ==================== USER TELEGRAM LINKING ====================

@router.post("/telegram/link")
async def link_telegram(current_user: dict = Depends(get_current_user)):
    """Generate link for user to connect their Telegram"""
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    telegram_pending_verifications[code] = {
        "user_id": current_user["id"],
        "type": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    bot_info = await telegram_service.get_bot_info()
    bot_username = bot_info.get("result", {}).get("username", "your_bot")
    
    return {
        "link": f"https://t.me/{bot_username}?start={code}",
        "code": code,
        "bot_username": bot_username
    }


@router.get("/telegram/status")
async def get_telegram_status(current_user: dict = Depends(get_current_user)):
    """Check if user has linked Telegram"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "telegram_chat_id": 1, "telegram_username": 1})
    return {
        "linked": bool(user.get("telegram_chat_id")),
        "username": user.get("telegram_username")
    }


@router.post("/telegram/unlink")
async def unlink_telegram(current_user: dict = Depends(get_current_user)):
    """Unlink Telegram from user account"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$unset": {"telegram_chat_id": "", "telegram_username": ""}}
    )
    return {"message": "Telegram отвязан"}


@router.post("/telegram/test")
async def test_telegram_notification(current_user: dict = Depends(get_current_user)):
    """Send test notification to user's Telegram"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "telegram_chat_id": 1, "name": 1})
    
    if not user.get("telegram_chat_id"):
        raise HTTPException(status_code=400, detail="Telegram не привязан")
    
    success = await telegram_service.send_telegram_message(
        user["telegram_chat_id"],
        f"<b>Тестовое уведомление</b>\n\nПривет, {user.get('name', 'пользователь')}! Уведомления работают корректно."
    )
    
    if success:
        return {"message": "Тестовое уведомление отправлено"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомления")


# ==================== CONTRACTOR TELEGRAM LINKING ====================

@router.post("/contractor/telegram/link")
async def link_contractor_telegram(current_user: dict = Depends(get_current_contractor)):
    """Generate link for contractor to connect their Telegram"""
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    telegram_pending_verifications[code] = {
        "user_id": current_user["id"],
        "type": "contractor",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    bot_info = await telegram_service.get_bot_info()
    bot_username = bot_info.get("result", {}).get("username", "your_bot")
    
    return {
        "link": f"https://t.me/{bot_username}?start={code}",
        "code": code,
        "bot_username": bot_username
    }


@router.get("/contractor/telegram/status")
async def get_contractor_telegram_status(contractor: dict = Depends(get_current_contractor)):
    """Check if contractor has linked Telegram"""
    c = await db.contractors.find_one({"id": contractor["id"]}, {"_id": 0, "telegram_chat_id": 1, "telegram_username": 1})
    return {
        "linked": bool(c.get("telegram_chat_id")),
        "username": c.get("telegram_username"),
        "chat_id": c.get("telegram_chat_id")
    }


@router.post("/contractor/telegram/unlink")
async def unlink_contractor_telegram(contractor: dict = Depends(get_current_contractor)):
    """Unlink Telegram from contractor account"""
    await db.contractors.update_one(
        {"id": contractor["id"]},
        {"$unset": {"telegram_chat_id": "", "telegram_username": ""}}
    )
    return {"message": "Telegram отвязан"}


@router.post("/contractor/telegram/test")
async def test_contractor_telegram(contractor: dict = Depends(get_current_contractor)):
    """Send test notification to contractor's Telegram"""
    c = await db.contractors.find_one({"id": contractor["id"]}, {"_id": 0, "telegram_chat_id": 1, "company_name": 1})
    if not c.get("telegram_chat_id"):
        raise HTTPException(status_code=400, detail="Telegram не привязан")
    success = await telegram_service.send_telegram_message(
        c["telegram_chat_id"],
        f"Тестовое сообщение от CarBridge\nКомпания: {c.get('company_name', '')}\nTelegram успешно привязан!"
    )
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка отправки")
    return {"message": "Тестовое сообщение отправлено"}


# ==================== ADMIN TELEGRAM ====================

@router.get("/admin/telegram/stats")
async def get_telegram_stats(current_user: dict = Depends(require_role(["admin"]))):
    """Get statistics about Telegram connections"""
    total_users = await db.users.count_documents({})
    linked_users = await db.users.count_documents({"telegram_chat_id": {"$exists": True, "$ne": None}})
    users_with_telegram_field = await db.users.count_documents({"telegram": {"$exists": True, "$ne": None, "$ne": ""}})
    
    total_contractors = await db.contractors.count_documents({})
    linked_contractors = await db.contractors.count_documents({"telegram_chat_id": {"$exists": True, "$ne": None}})
    contractors_with_telegram_field = await db.contractors.count_documents({"telegram": {"$exists": True, "$ne": None, "$ne": ""}})
    
    unlinked_users = await db.users.find(
        {"telegram": {"$exists": True, "$ne": None, "$ne": ""}, "telegram_chat_id": {"$exists": False}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "telegram": 1}
    ).to_list(100)
    
    unlinked_contractors = await db.contractors.find(
        {"telegram": {"$exists": True, "$ne": None, "$ne": ""}, "telegram_chat_id": {"$exists": False}},
        {"_id": 0, "id": 1, "company_name": 1, "email": 1, "telegram": 1}
    ).to_list(100)
    
    return {
        "users": {
            "total": total_users,
            "linked": linked_users,
            "with_telegram_username": users_with_telegram_field,
            "unlinked_with_username": len(unlinked_users)
        },
        "contractors": {
            "total": total_contractors,
            "linked": linked_contractors,
            "with_telegram_username": contractors_with_telegram_field,
            "unlinked_with_username": len(unlinked_contractors)
        },
        "unlinked_users": unlinked_users,
        "unlinked_contractors": unlinked_contractors
    }


@router.post("/admin/telegram/send-invites")
async def send_telegram_invites(current_user: dict = Depends(require_role(["admin"]))):
    """Send invitation messages to all linked Telegram users"""
    results = {"users_notified": 0, "contractors_notified": 0, "errors": []}
    
    linked_users = await db.users.find(
        {"telegram_chat_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "telegram_chat_id": 1, "name": 1}
    ).to_list(500)
    
    for user in linked_users:
        try:
            success = await telegram_service.send_telegram_message(
                user["telegram_chat_id"],
                f"Привет, {user.get('name', 'пользователь')}!\n\n"
                "Это напоминание о том, что ваш Telegram подключен к CarBridge.\n"
                "Вы будете получать уведомления о сделках и сообщениях.\n\n"
                "/chats - Показать активные чаты"
            )
            if success:
                results["users_notified"] += 1
        except Exception as e:
            results["errors"].append(f"User {user.get('name')}: {str(e)}")
    
    linked_contractors = await db.contractors.find(
        {"telegram_chat_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "telegram_chat_id": 1, "company_name": 1}
    ).to_list(500)
    
    for contractor_item in linked_contractors:
        try:
            success = await telegram_service.send_telegram_message(
                contractor_item["telegram_chat_id"],
                f"Привет, {contractor_item.get('company_name', 'подрядчик')}!\n\n"
                "Это напоминание о том, что ваш Telegram подключен к CarBridge.\n"
                "Вы будете получать уведомления о тендерах и сообщениях клиентов.\n\n"
                "/chats - Показать активные чаты"
            )
            if success:
                results["contractors_notified"] += 1
        except Exception as e:
            results["errors"].append(f"Contractor {contractor_item.get('company_name')}: {str(e)}")
    
    return results
