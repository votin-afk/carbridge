"""Deal management routes - CRUD, stages, messages, files, contractor interactions"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from datetime import datetime, timezone
import uuid
import jwt
import logging

import sys
sys.path.insert(0, '/app/backend')

from database import db
from config import (
    UPLOADS_DIR, MAX_FILE_SIZE, JWT_SECRET, JWT_ALGORITHM,
    DEAL_ADD_FEE, CONSULTANT_FEE, PLATFORM_COMMISSION, PLATFORM_PAYMENT_FEE,
    COMMISSION_RATE, AFFILIATE_SHARE, PARTNER_THRESHOLD, NEW_DEAL_STAGES
)
from utils.auth import get_current_user, get_current_contractor
from services import telegram_service
from services.bitrix24 import get_bitrix24

logger = logging.getLogger(__name__)

router = APIRouter(tags=["deals"])

@router.post("/deals/create")
async def create_deal(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new deal from a car in garage"""
    car_id = data.get("car_id")
    
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    # Check if user is verified
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    if not account or not account.get("is_verified"):
        raise HTTPException(status_code=403, detail="Для создания сделки необходима верификация")
    
    deal_id = str(uuid.uuid4())
    
    deal_doc = {
        "id": deal_id,
        "user_id": current_user["id"],
        "car_id": car_id,
        "car_info": {
            "brand": car.get("brand"),
            "model": car.get("model"),
            "year": car.get("year"),
            "price_cny": car.get("price_cny"),
            "calculated_price_usd": car.get("calculated_price_usd"),
            "image_url": car.get("image_url", "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800")
        },
        "status": "active",
        "current_stage": "verification",
        "can_proceed": False,  # Needs moderator approval
        "stage_approvals": {},
        "stages": {
            "verification": {"status": "pending", "moderator_approved": False},
            "contract": {"status": "pending", "moderator_approved": False},
            "inspection": {"status": "pending", "moderator_approved": False},
            "payment": {"status": "pending", "moderator_approved": False},
            "export": {"status": "pending", "moderator_approved": False},
            "logistics": {"status": "pending", "moderator_approved": False},
            "delivery": {"status": "pending", "moderator_approved": False}
        },
        "contractors": car.get("contractors", {}),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deals.insert_one(deal_doc)
    
    # Update car status
    await db.garage.update_one(
        {"id": car_id},
        {"$set": {"status": "in_deal", "deal_id": deal_id}}
    )
    
    return {
        "message": "Сделка создана",
        "deal_id": deal_id,
        "current_stage": "verification"
    }

@router.get("/deals")
async def get_user_deals(current_user: dict = Depends(get_current_user)):
    """Get all deals for current user"""
    deals = await db.deals.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return deals

@router.get("/deals/completed")
async def get_completed_deals(current_user: dict = Depends(get_current_user)):
    """Get all completed deals (purchased cars) for user"""
    completed_deals = await db.deals.find(
        {"user_id": current_user["id"], "status": "completed"},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(100)
    
    # Build garage image map for fallback
    garage_cars = await db.garage.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "id": 1, "brand": 1, "model": 1, "image_url": 1}
    ).to_list(100)
    garage_by_id = {g["id"]: g for g in garage_cars}
    garage_image_map = {}
    for gc in garage_cars:
        img = gc.get("image_url", "")
        if img and "unsplash.com" not in img:
            key = (gc.get("brand", "").lower(), gc.get("model", "").lower())
            garage_image_map[key] = img
    
    for deal in completed_deals:
        car_id = deal.get("car_id")
        if car_id and car_id in garage_by_id:
            deal["car_details"] = garage_by_id[car_id]
        
        # Fix image_url: use garage real image over stock
        ci = deal.get("car_info") or {}
        cd = deal.get("car_details") or {}
        best_image = None
        
        # Priority: car_details real image > car_info real image > garage brand match
        for source in [cd.get("image_url"), ci.get("image_url")]:
            if source and "unsplash.com" not in source:
                best_image = source
                break
        
        if not best_image:
            brand = (ci.get("brand") or "").lower()
            model = (ci.get("model") or "").lower()
            best_image = garage_image_map.get((brand, model))
            if not best_image:
                for (gb, gm), gimg in garage_image_map.items():
                    if gb and gb == brand:
                        best_image = gimg
                        break
        
        if best_image:
            if isinstance(ci, dict):
                ci["image_url"] = best_image
                deal["car_info"] = ci
            if isinstance(cd, dict):
                cd["image_url"] = best_image
                deal["car_details"] = cd
    
    return completed_deals

@router.get("/deals/{deal_id}")
async def get_deal(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific deal for current user"""
    deal = await db.deals.find_one(
        {"id": deal_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    return deal

# ==================== DEAL MANAGEMENT ENDPOINTS ====================


@router.post("/deals/add-car")
async def add_car_to_deal(data: dict, current_user: dict = Depends(get_current_user)):
    """Add car to deal from garage (charges $300) or from tender (free)"""
    car_id = data.get("car_id")
    from_tender = data.get("from_tender", False)
    tender_offer_id = data.get("tender_offer_id")
    tender_id = data.get("tender_id")
    
    # Check verification
    verification = await db.verifications.find_one({"user_id": current_user["id"]})
    if not verification or verification.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Для создания сделки необходима верификация")
    
    # Check contract signed
    if not verification.get("contract_signed"):
        raise HTTPException(status_code=403, detail="Необходимо подписать договор")
    
    # Get account for balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    # Charge $300 if not from tender
    if not from_tender:
        if balance < DEAL_ADD_FEE:
            raise HTTPException(status_code=400, detail=f"Недостаточно средств. Необходимо ${DEAL_ADD_FEE}, баланс: ${balance}")
        
        # Deduct fee
        await db.accounts.update_one(
            {"user_id": current_user["id"]},
            {"$inc": {"balance": -DEAL_ADD_FEE}}
        )
        
        # Log transaction
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "type": "deal_fee",
            "amount": -DEAL_ADD_FEE,
            "description": "Добавление авто в сделку",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Get car info - try garage first
    car = None
    if car_id:
        car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    
    # If car not found and this is from tender, try to get car info from tender offer
    if not car and from_tender and tender_offer_id:
        offer = await db.contractor_offers.find_one({"id": tender_offer_id})
        if not offer:
            # Try tender_offers collection
            offer = await db.tender_offers.find_one({"id": tender_offer_id})
        
        # Also check mock offers inside tender
        if not offer and tender_id:
            tender_doc = await db.tenders.find_one({"id": tender_id})
            if tender_doc:
                mock_offers = tender_doc.get("offers", [])
                for mock_offer in mock_offers:
                    if mock_offer.get("id") == tender_offer_id:
                        offer = mock_offer
                        break
        
        if offer:
            # Get tender to extract car_request info (brand, model) and car_info
            tender = await db.tenders.find_one({"id": tender_id or offer.get("tender_id")})
            car_request = tender.get("car_request", {}) if tender else {}
            car_info = tender.get("car_info", {}) if tender else {}
            
            # Create car info from offer data + tender car_request/car_info
            car = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "brand": offer.get("car_brand") or car_info.get("brand") or car_request.get("brand", "N/A"),
                "model": offer.get("car_model") or car_info.get("model") or car_request.get("model", ""),
                "year": offer.get("car_year") or car_info.get("year") or car_request.get("year_to") or car_request.get("year_from"),
                "price_cny": offer.get("price_cny") or car_info.get("price_cny", 0),
                "price_usd": offer.get("price_usd") or offer.get("price") or car_info.get("price_usd", 0),
                "calculated_price_usd": offer.get("price_usd") or offer.get("price") or car_info.get("calculated_price_usd", 0),
                "engine_type": offer.get("engine_type") or car_info.get("engine_type") or car_request.get("engine_type", "ice"),
                "engine_volume": offer.get("engine_volume") or car_info.get("engine_volume"),
                "mileage": offer.get("mileage") or car_info.get("mileage"),
                "image_url": (offer.get("car_photos", [""])[0] if offer.get("car_photos") else None) or offer.get("image_url") or car_info.get("image_url", ""),
                "source_url": offer.get("car_link") or offer.get("source_url") or car_info.get("source_url", ""),
                "description": offer.get("car_details") or offer.get("description") or car_info.get("description", ""),
                "from_tender_offer": True,
                "tender_offer_id": tender_offer_id,
                "contractor_name": offer.get("contractor_name"),
                "status": "in_deal",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            # Save to garage
            await db.garage.insert_one(car)
            car_id = car["id"]
            logger.info(f"Created garage entry from tender offer: {car_id}, brand={car['brand']}, model={car['model']}")
    
    # If still no car, try to get from tender's car_info
    if not car and from_tender and tender_id:
        tender = await db.tenders.find_one({"id": tender_id, "user_id": current_user["id"]})
        if tender and tender.get("car_info"):
            car = tender["car_info"]
            car_id = car.get("id")
    
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    # Create deal
    deal_id = str(uuid.uuid4())
    
    # Default stages structure
    stages = {
        "leasing": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "inspection": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "export": {"status": "pending", "completed": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "logistics_china": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "insurance": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "delivery_rb": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "customs": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "contractor_name": None, "price": None, "locked": False, "moderator_confirmed": False},
        "completion": {"status": "pending", "completed": False, "moderator_confirmed": False}
    }
    
    contractor_info = {}
    
    # If from tender with selected offer, pre-fill stages from offer
    if from_tender and tender_offer_id:
        # Search for offer in multiple places
        offer = await db.contractor_offers.find_one({"id": tender_offer_id})
        if not offer:
            offer = await db.tender_offers.find_one({"id": tender_offer_id})
        
        # Also check mock offers in tender
        if not offer and tender_id:
            tender_doc = await db.tenders.find_one({"id": tender_id})
            if tender_doc:
                for mock_offer in tender_doc.get("offers", []):
                    if mock_offer.get("id") == tender_offer_id:
                        offer = mock_offer
                        break
        
        if offer:
            contractor_id = offer.get("contractor_id")
            contractor_name = offer.get("contractor_name")
            
            # Get contractor info from DB if we have contractor_id
            if contractor_id:
                contractor = await db.contractors.find_one({"id": contractor_id})
                if contractor:
                    contractor_name = contractor.get("company_name", contractor_name)
            
            contractor_info = {
                "id": contractor_id,
                "name": contractor_name
            }
            
            # Get services from offer
            included_services = offer.get("included_services", {})
            service_prices = offer.get("service_prices", {})
            services_list = offer.get("services", [])  # New format with array of services
            
            logger.info(f"Processing offer services: included={included_services}, prices={service_prices}")
            
            # Process services from offer and assign contractor to those stages
            if services_list:
                # New format: array of {stage, price} objects
                for svc in services_list:
                    stage_key = svc.get("stage")
                    if stage_key and stage_key in stages:
                        stages[stage_key]["contractor_id"] = contractor_id
                        stages[stage_key]["contractor_name"] = contractor_name
                        stages[stage_key]["price"] = float(svc.get("price", 0)) if svc.get("price") else None
                        stages[stage_key]["locked"] = True  # Cannot change contractor
                        stages[stage_key]["status"] = "contractor_assigned"
                        stages[stage_key]["assigned_at"] = datetime.now(timezone.utc).isoformat()
            elif included_services:
                # Old format: included_services dict
                for svc_key, is_included in included_services.items():
                    if is_included and svc_key in stages:
                        price_val = service_prices.get(svc_key)
                        stages[svc_key]["contractor_id"] = contractor_id
                        stages[svc_key]["contractor_name"] = contractor_name
                        stages[svc_key]["price"] = float(price_val) if price_val else None
                        stages[svc_key]["locked"] = True  # Cannot change contractor - from tender offer
                        stages[svc_key]["status"] = "contractor_assigned"
                        stages[svc_key]["assigned_at"] = datetime.now(timezone.utc).isoformat()
                        logger.info(f"Assigned contractor {contractor_name} to stage {svc_key} with price {price_val}")
            
            # Create document exchange card for this deal
            doc_card = {
                "id": str(uuid.uuid4()),
                "deal_id": deal_id,
                "user_id": current_user["id"],
                "contractor_id": contractor_id,
                "type": "deal_documents",
                "title": f"Документы: {car.get('brand', '')} {car.get('model', '')}",
                "files": [],
                "messages": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.deal_documents.insert_one(doc_card)
    
    deal_doc = {
        "id": deal_id,
        "user_id": current_user["id"],
        "car_id": car_id,
        "tender_offer_id": tender_offer_id,
        "from_tender": from_tender,
        "contractor": contractor_info,
        "car_info": {
            "brand": car.get("brand"),
            "model": car.get("model"),
            "year": car.get("year"),
            "price_cny": car.get("price_cny"),
            "price_usd": car.get("calculated_price_usd") or car.get("price_usd"),
            "image_url": car.get("image_url") or "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800"
        },
        "status": "active",
        "current_stage": "leasing",
        "stages": stages,
        "contractors": {},
        "payments": [],
        "total_paid": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deals.insert_one(deal_doc)
    
    # Update car status
    await db.garage.update_one(
        {"id": car_id},
        {"$set": {"status": "in_deal", "deal_id": deal_id}}
    )
    
    return {
        "message": "Автомобиль добавлен в сделку",
        "deal_id": deal_id,
        "fee_charged": 0 if from_tender else DEAL_ADD_FEE
    }

@router.post("/deals/{deal_id}/select-contractor")
async def select_contractor_for_stage(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Select contractor for a deal stage"""
    stage = data.get("stage")  # inspection, export, logistics
    contractor_id = data.get("contractor_id")
    price = data.get("price", 0)
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Allowed stages for contractor selection
    allowed_stages = ["leasing", "inspection", "export", "logistics_china", "insurance", "delivery_rb", "customs"]
    if stage not in allowed_stages:
        raise HTTPException(status_code=400, detail="Неверный этап")
    
    # Get contractor info
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    contractor_name = contractor.get("company_name", "") or contractor.get("name", "") if contractor else ""
    contractor_email = contractor.get("email", "") if contractor else ""
    
    # Update deal with contractor selection - requires moderator approval
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.contractor_id": contractor_id,
                f"stages.{stage}.contractor_name": contractor_name,
                f"stages.{stage}.price": price,
                f"stages.{stage}.status": "pending_moderation",
                f"stages.{stage}.awaiting_approval": True,
                f"stages.{stage}.assigned_at": datetime.now(timezone.utc).isoformat(),
                f"contractors.{stage}": contractor_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Create notification for contractor
    stage_labels = {
        "leasing": "Лизинг",
        "inspection": "Инспекция авто",
        "export": "Выкуп и экспорт",
        "logistics_china": "Доставка до порта (Китай)",
        "insurance": "Страхование авто",
        "delivery_rb": "Доставка в Беларусь",
        "customs": "Таможенное оформление"
    }
    
    notification = {
        "id": str(uuid.uuid4()),
        "contractor_id": contractor_id,
        "deal_id": deal_id,
        "type": "contractor_selected",
        "title": f"Вас выбрали на этап: {stage_labels.get(stage, stage)}",
        "message": f"Клиент выбрал вас для выполнения этапа '{stage_labels.get(stage, stage)}'. Стоимость: ${price}. Свяжитесь с клиентом для обсуждения деталей.",
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    # Send Telegram notification to contractor
    if contractor and contractor.get("telegram_chat_id"):
        car_info = deal.get("car_info", {})
        car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "Авто"
        client_name = current_user.get("name", "Клиент")
        await telegram_service.notify_contractor_assigned(
            contractor["telegram_chat_id"],
            car_name,
            stage,
            client_name
        )
    
    # Send Telegram notification to moderators about pending approval
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            car_info = deal.get("car_info", {})
            car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "Авто"
            await telegram_service.notify_moderators_contractor_assignment(
                moderator_chat_ids,
                current_user.get("name", "Клиент"),
                car_name,
                stage,
                contractor_name,
                price
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
    # Bitrix24: Create task for contractor assignment
    b24 = get_bitrix24()
    if b24:
        try:
            car_info = deal.get("car_info", {})
            asyncio.create_task(b24.create_deal(
                title=f"Этап сделки: {stage_labels.get(stage, stage)} - {car_info.get('brand', '')} {car_info.get('model', '')}",
                description=f"Подрядчик: {contractor_name}\nЭтап: {stage_labels.get(stage, stage)}\nСтоимость: ${price}",
                contact_email=current_user.get("email"),
                contact_phone=current_user.get("phone"),
                amount=price,
                source="contractor_selection",
                stage="execution"
            ))
        except Exception as e:
            logger.error(f"Bitrix24 deal creation error: {e}")
    
    return {"message": f"Подрядчик выбран для этапа {stage}", "contractor_name": contractor_name}

@router.post("/deals/{deal_id}/pay-stage")
async def pay_deal_stage(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Pay for a deal stage from user balance"""
    stage = data.get("stage")
    amount = data.get("amount", 0)
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Get account balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < amount:
        raise HTTPException(status_code=400, detail=f"Недостаточно средств. Необходимо ${amount}, баланс: ${balance}")
    
    # Deduct from balance
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -amount}}
    )
    
    # Update deal
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.paid": True,
                f"stages.{stage}.paid_amount": amount,
                f"stages.{stage}.paid_at": datetime.now(timezone.utc).isoformat()
            },
            "$inc": {"total_paid": amount},
            "$push": {
                "payments": {
                    "id": str(uuid.uuid4()),
                    "stage": stage,
                    "amount": amount,
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }
    )
    
    # Log transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "deal_id": deal_id,
        "type": "stage_payment",
        "stage": stage,
        "amount": -amount,
        "description": f"Оплата этапа: {stage}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send Telegram notification to contractor about payment
    stage_data = deal.get("stages", {}).get(stage, {})
    contractor_id = stage_data.get("contractor_id")
    if contractor_id:
        contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0, "telegram_chat_id": 1, "company_name": 1})
        if contractor and contractor.get("telegram_chat_id"):
            car_info = deal.get("car_info", {})
            car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "Авто"
            await telegram_service.notify_stage_status_change(
                contractor["telegram_chat_id"],
                car_name,
                stage,
                "paid",
                None
            )
    
    return {"message": "Оплата прошла успешно", "new_balance": balance - amount}

@router.post("/deals/{deal_id}/skip-leasing")
async def skip_leasing_stage(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Skip leasing request stage"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                "stages.leasing_request.skipped": True,
                "stages.leasing_request.completed": True,
                "current_stage": "inspection",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Этап лизинга пропущен"}

@router.post("/deals/{deal_id}/request-leasing")
async def request_leasing(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Request leasing quote"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                "stages.leasing_request.requested": True,
                "stages.leasing_request.leasing_company_id": data.get("leasing_company_id"),
                "stages.leasing_request.requested_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Запрос на лизинг отправлен"}

@router.post("/deals/{deal_id}/complete-stage")
async def complete_deal_stage(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Mark stage as completed (awaits moderator confirmation)"""
    stage = data.get("stage")
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.user_completed": True,
                f"stages.{stage}.awaiting_moderator": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Этап отмечен как выполненный, ожидает подтверждения модератора"}

@router.post("/deals/{deal_id}/update-stage-price")
async def update_stage_price(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update price for a stage (before payment)"""
    stage = data.get("stage")
    new_price = data.get("price")
    reason = data.get("reason", "")
    
    if not stage or new_price is None:
        raise HTTPException(status_code=400, detail="Укажите этап и новую стоимость")
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if stage is already paid
    stage_data = deal.get("stages", {}).get(stage, {})
    if stage_data.get("paid"):
        raise HTTPException(status_code=400, detail="Этап уже оплачен, изменение стоимости невозможно")
    
    old_price = stage_data.get("price", 0)
    
    # Log price change
    price_change_log = {
        "id": str(uuid.uuid4()),
        "stage": stage,
        "old_price": old_price,
        "new_price": new_price,
        "reason": reason,
        "changed_by": current_user["id"],
        "changed_by_name": f"{current_user.get('name', '')} {current_user.get('last_name', '')}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.price": new_price,
                f"stages.{stage}.price_modified": True,
                f"stages.{stage}.price_change_reason": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "price_changes": price_change_log
            }
        }
    )
    
    return {
        "message": "Стоимость этапа обновлена",
        "old_price": old_price,
        "new_price": new_price
    }

# ==================== NEW DEAL STAGES ENDPOINTS ====================

@router.post("/deals/{deal_id}/skip-stage")
async def skip_deal_stage(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Skip an optional stage"""
    stage = data.get("stage")
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if stage is optional
    optional_stages = ["leasing", "inspection", "logistics_china", "insurance", "delivery_rb", "customs"]
    if stage not in optional_stages:
        raise HTTPException(status_code=400, detail="Этот этап нельзя пропустить")
    
    # Find next stage
    current_idx = NEW_DEAL_STAGES.index(stage) if stage in NEW_DEAL_STAGES else 0
    next_stage = NEW_DEAL_STAGES[current_idx + 1] if current_idx < len(NEW_DEAL_STAGES) - 1 else "completion"
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.skipped": True,
                f"stages.{stage}.completed": True,
                "current_stage": next_stage,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": f"Этап '{stage}' пропущен", "next_stage": next_stage}

@router.post("/deals/{deal_id}/leasing-request")
async def submit_leasing_request(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Submit leasing request to selected companies"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    term = data.get("term", 36)
    down_payment_percent = data.get("down_payment_percent", 20)
    loan_amount = data.get("loan_amount", 0)
    selected_companies = data.get("selected_companies", [])
    
    if not selected_companies:
        raise HTTPException(status_code=400, detail="Выберите хотя бы одну лизинговую компанию")
    
    # Create leasing requests
    leasing_requests = []
    for company_id in selected_companies:
        leasing_requests.append({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "term": term,
            "down_payment_percent": down_payment_percent,
            "loan_amount": loan_amount,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                "stages.leasing.requested": True,
                "stages.leasing.leasing_requests": leasing_requests,
                "stages.leasing.term": term,
                "stages.leasing.down_payment_percent": down_payment_percent,
                "stages.leasing.completed": True,
                "current_stage": "inspection",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"Заявки на лизинг отправлены в {len(selected_companies)} компаний",
        "next_stage": "inspection"
    }

@router.post("/deals/{deal_id}/pay-invoice")
async def pay_deal_invoice(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Pay invoice for a deal stage"""
    stage = data.get("stage")
    amount = data.get("amount", 0)
    through_platform = data.get("through_platform", False)
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if through_platform:
        # Get account balance
        account = await db.accounts.find_one({"user_id": current_user["id"]})
        balance = account.get("balance", 0) if account else 0
        
        if balance < amount:
            raise HTTPException(status_code=400, detail=f"Недостаточно средств. Необходимо ${amount:.2f}, баланс: ${balance:.2f}")
        
        # Deduct from balance
        await db.accounts.update_one(
            {"user_id": current_user["id"]},
            {"$inc": {"balance": -amount}}
        )
        
        # Log transaction
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "deal_id": deal_id,
            "type": "stage_payment",
            "stage": stage,
            "amount": -amount,
            "payment_method": "platform",
            "description": f"Оплата этапа: {stage}",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Find next stage
    current_idx = NEW_DEAL_STAGES.index(stage) if stage in NEW_DEAL_STAGES else 0
    next_stage = NEW_DEAL_STAGES[current_idx + 1] if current_idx < len(NEW_DEAL_STAGES) - 1 else "completion"
    
    # Update deal
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.paid": True,
                f"stages.{stage}.paid_amount": amount,
                f"stages.{stage}.paid_through_platform": through_platform,
                f"stages.{stage}.paid_at": datetime.now(timezone.utc).isoformat(),
                f"stages.{stage}.completed": True,
                "current_stage": next_stage,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$inc": {"total_paid": amount},
            "$push": {
                "payments": {
                    "id": str(uuid.uuid4()),
                    "stage": stage,
                    "amount": amount,
                    "through_platform": through_platform,
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }
    )
    
    return {
        "message": "Оплата прошла успешно" if through_platform else "Счёт отмечен как оплаченный",
        "next_stage": next_stage
    }

@router.post("/deals/{deal_id}/complete")
async def complete_deal(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Complete the deal and process affiliate commission"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if already completed
    if deal.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Сделка уже завершена")
    
    # Check if export stage is completed (minimum requirement)
    export_stage = deal.get("stages", {}).get("export", {})
    if not export_stage.get("completed") and not export_stage.get("paid"):
        raise HTTPException(status_code=400, detail="Для завершения сделки необходимо завершить этап 'Экспорт'")
    
    total_paid = deal.get("total_paid", 0)
    completed_at = datetime.now(timezone.utc).isoformat()
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                "status": "completed",
                "stages.completion.completed": True,
                "current_stage": "completed",
                "completed_at": completed_at,
                "updated_at": completed_at
            }
        }
    )
    
    # Update car status
    await db.garage.update_one(
        {"id": deal.get("car_id")},
        {"$set": {"status": "delivered"}}
    )
    
    # Process affiliate commission if user is a referral
    user = await db.users.find_one({"id": current_user["id"]})
    affiliate_commission = 0
    if user and user.get("referred_by"):
        affiliate_id = user["referred_by"]
        
        # Calculate commission (20% of 3% platform commission)
        platform_commission = total_paid * COMMISSION_RATE
        affiliate_commission = platform_commission * AFFILIATE_SHARE
        
        # Update referral stats
        await db.referrals.update_one(
            {"referral_id": current_user["id"]},
            {
                "$inc": {
                    "completed_deals": 1,
                    "total_commission": affiliate_commission
                }
            }
        )
        
        # Update affiliate stats and balance
        update_result = await db.affiliates.find_one_and_update(
            {"user_id": affiliate_id},
            {
                "$inc": {
                    "completed_deals": 1,
                    "total_earnings": affiliate_commission,
                    "available_balance": affiliate_commission
                }
            },
            return_document=True
        )
        
        # Check if affiliate should become partner (3+ completed deals)
        if update_result and update_result.get("completed_deals", 0) >= PARTNER_THRESHOLD and not update_result.get("is_partner"):
            await db.affiliates.update_one(
                {"user_id": affiliate_id},
                {"$set": {"is_partner": True, "partner_since": completed_at}}
            )
        
        # Also credit the affiliate's main account balance
        await db.accounts.update_one(
            {"user_id": affiliate_id},
            {"$inc": {"balance": affiliate_commission}},
            upsert=True
        )
        
        # Record transaction
        transaction_doc = {
            "id": str(uuid.uuid4()),
            "affiliate_id": affiliate_id,
            "type": "commission",
            "amount": affiliate_commission,
            "deal_id": deal_id,
            "referral_id": current_user["id"],
            "referral_name": user.get("name", ""),
            "description": f"Комиссия со сделки реферала: ${total_paid:,.2f}",
            "created_at": completed_at
        }
        await db.affiliate_transactions.insert_one(transaction_doc)
    
    return {
        "message": "Сделка успешно завершена!",
        "affiliate_commission_paid": affiliate_commission
    }

# ==================== END NEW DEAL STAGES ENDPOINTS ====================

# ==================== DEAL MESSAGES & FILES API ====================

@router.get("/deals/{deal_id}/messages")
async def get_deal_messages(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Get all messages for a deal"""
    # Check if user has access to this deal
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # User can be the deal owner
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    messages = await db.deal_messages.find(
        {"deal_id": deal_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return messages

@router.post("/deals/{deal_id}/messages")
async def send_deal_message(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Send a message in a deal chat"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "deal_id": deal_id,
        "sender_id": current_user["id"],
        "sender_name": current_user.get("name", current_user.get("email", "Пользователь")),
        "sender_type": "client",
        "content": data.get("content", ""),
        "file_ids": data.get("file_ids", []),
        "stage_key": data.get("stage_key"),
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_messages.insert_one(message)
    
    return {"message": "Сообщение отправлено", "id": message_id}

@router.get("/deals/{deal_id}/files")
async def get_deal_files(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Get all files for a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    files = await db.deal_files.find(
        {"deal_id": deal_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return files

@router.post("/deals/{deal_id}/files")
async def upload_deal_file(
    deal_id: str,
    file: UploadFile = File(...),
    stage_key: str = Form(None),
    file_type: str = Form("document"),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file for a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 50MB)")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    safe_filename = f"{file_id}{file_ext}"
    
    # Create deal directory
    deal_dir = UPLOADS_DIR / deal_id
    deal_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = deal_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Determine file category
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    video_exts = [".mp4", ".mov", ".avi", ".webm"]
    doc_exts = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
    
    if file_ext in image_exts:
        category = "photo"
    elif file_ext in video_exts:
        category = "video"
    elif file_ext in doc_exts:
        category = "document"
    else:
        category = "other"
    
    # Save file info to database
    file_doc = {
        "id": file_id,
        "deal_id": deal_id,
        "uploader_id": current_user["id"],
        "uploader_name": current_user.get("name", current_user.get("email", "Пользователь")),
        "uploader_type": "client",
        "original_name": file.filename,
        "saved_name": safe_filename,
        "file_type": file_type,
        "category": category,
        "stage_key": stage_key,
        "description": description,
        "size": len(file_content),
        "mime_type": file.content_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_files.insert_one(file_doc)
    
    return {
        "message": "Файл загружен",
        "file_id": file_id,
        "filename": file.filename,
        "size": len(file_content)
    }

@router.get("/deals/{deal_id}/files/{file_id}/download")
async def download_deal_file(deal_id: str, file_id: str, token: str = None, current_user: dict = Depends(get_current_user)):
    """Download a file from a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    file_doc = await db.deal_files.find_one({"id": file_id, "deal_id": deal_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    file_path = UPLOADS_DIR / deal_id / file_doc["saved_name"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на сервере")
    
    return FileResponse(
        path=str(file_path),
        filename=file_doc["original_name"],
        media_type=file_doc.get("mime_type", "application/octet-stream")
    )

@router.get("/files/{file_id}/public-download")
async def public_download_file(file_id: str, token: str = None):
    """Download a file using token in query parameter (for browser-native downloads)"""
    if not token:
        raise HTTPException(status_code=401, detail="Токен обязателен")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject_id = payload.get("sub")
        token_type = payload.get("type")
        if not subject_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    file_doc = await db.deal_files.find_one({"id": file_id}, {"_id": 0})
    if not file_doc:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    deal_id = file_doc["deal_id"]
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    has_access = False
    
    if token_type == "contractor":
        contractor = await db.contractors.find_one({"id": subject_id})
        if contractor:
            stages = deal.get("stages", {})
            for sv in stages.values():
                if sv.get("contractor_id") == contractor["id"]:
                    has_access = True
                    break
    else:
        user = await db.users.find_one({"id": subject_id})
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        is_owner = deal.get("user_id") == subject_id
        is_mod = user.get("role") in ["moderator", "admin"]
        has_access = is_owner or is_mod
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    file_path = UPLOADS_DIR / deal_id / file_doc["saved_name"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на сервере")
    
    return FileResponse(
        path=str(file_path),
        filename=file_doc["original_name"],
        media_type=file_doc.get("mime_type", "application/octet-stream")
    )

@router.delete("/deals/{deal_id}/files/{file_id}")
async def delete_deal_file(deal_id: str, file_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a file from a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    file_doc = await db.deal_files.find_one({"id": file_id, "deal_id": deal_id, "uploader_id": current_user["id"]})
    if not file_doc:
        raise HTTPException(status_code=404, detail="Файл не найден или вы не можете его удалить")
    
    # Delete file from disk
    file_path = UPLOADS_DIR / deal_id / file_doc["saved_name"]
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    await db.deal_files.delete_one({"id": file_id})
    
    return {"message": "Файл удалён"}

# ==================== CONTRACTOR DEAL MESSAGES & FILES ====================

@router.get("/contractor/deals/{deal_id}/messages")
async def get_contractor_deal_messages(deal_id: str, current_user: dict = Depends(get_current_contractor)):
    """Get messages for a deal (contractor view)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if contractor has access (is assigned to any stage)
    has_access = False
    stages = deal.get("stages", {})
    for stage_data in stages.values():
        if stage_data.get("contractor_id") == current_user["id"]:
            has_access = True
            break
    
    if not has_access and deal.get("contractor", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    messages = await db.deal_messages.find(
        {"deal_id": deal_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return messages

@router.post("/contractor/deals/{deal_id}/messages")
async def send_contractor_deal_message(deal_id: str, data: dict, current_user: dict = Depends(get_current_contractor)):
    """Send a message in a deal chat (contractor)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check access
    has_access = False
    stages = deal.get("stages", {})
    for stage_data in stages.values():
        if stage_data.get("contractor_id") == current_user["id"]:
            has_access = True
            break
    
    if not has_access and deal.get("contractor", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "deal_id": deal_id,
        "sender_id": current_user["id"],
        "sender_name": current_user.get("company_name", "Подрядчик"),
        "sender_type": "contractor",
        "content": data.get("content", ""),
        "file_ids": data.get("file_ids", []),
        "stage_key": data.get("stage_key"),
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_messages.insert_one(message)
    
    return {"message": "Сообщение отправлено", "id": message_id}

@router.get("/contractor/deals/{deal_id}/files")
async def get_contractor_deal_files(deal_id: str, current_user: dict = Depends(get_current_contractor)):
    """Get all files for a deal (contractor view)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check access
    has_access = False
    stages = deal.get("stages", {})
    for stage_data in stages.values():
        if stage_data.get("contractor_id") == current_user["id"]:
            has_access = True
            break
    
    if not has_access and deal.get("contractor", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    files = await db.deal_files.find(
        {"deal_id": deal_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return files

@router.post("/contractor/deals/{deal_id}/files")
async def upload_contractor_deal_file(
    deal_id: str,
    file: UploadFile = File(...),
    stage_key: str = Form(None),
    file_type: str = Form("document"),
    description: str = Form(""),
    current_user: dict = Depends(get_current_contractor)
):
    """Upload a file for a deal (contractor)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check access
    has_access = False
    stages = deal.get("stages", {})
    for stage_data in stages.values():
        if stage_data.get("contractor_id") == current_user["id"]:
            has_access = True
            break
    
    if not has_access and deal.get("contractor", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 50MB)")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    safe_filename = f"{file_id}{file_ext}"
    
    # Create deal directory
    deal_dir = UPLOADS_DIR / deal_id
    deal_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = deal_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Determine file category
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    video_exts = [".mp4", ".mov", ".avi", ".webm"]
    doc_exts = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
    
    if file_ext in image_exts:
        category = "photo"
    elif file_ext in video_exts:
        category = "video"
    elif file_ext in doc_exts:
        category = "document"
    else:
        category = "other"
    
    # Save file info to database
    file_doc = {
        "id": file_id,
        "deal_id": deal_id,
        "uploader_id": current_user["id"],
        "uploader_name": current_user.get("company_name", "Подрядчик"),
        "uploader_type": "contractor",
        "original_name": file.filename,
        "saved_name": safe_filename,
        "file_type": file_type,
        "category": category,
        "stage_key": stage_key,
        "description": description,
        "size": len(file_content),
        "mime_type": file.content_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_files.insert_one(file_doc)
    
    return {
        "message": "Файл загружен",
        "file_id": file_id,
        "filename": file.filename,
        "size": len(file_content)
    }

@router.get("/contractor/deals/{deal_id}/files/{file_id}/download")
async def download_contractor_deal_file(deal_id: str, file_id: str, current_user: dict = Depends(get_current_contractor)):
    """Download a file from a deal (contractor)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check access
    has_access = False
    stages = deal.get("stages", {})
    for stage_data in stages.values():
        if stage_data.get("contractor_id") == current_user["id"]:
            has_access = True
            break
    
    if not has_access and deal.get("contractor", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    file_doc = await db.deal_files.find_one({"id": file_id, "deal_id": deal_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    file_path = UPLOADS_DIR / deal_id / file_doc["saved_name"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на сервере")
    
    return FileResponse(
        path=str(file_path),
        filename=file_doc["original_name"],
        media_type=file_doc.get("mime_type", "application/octet-stream")
    )

@router.get("/contractor/deals")
async def get_contractor_deals(current_user: dict = Depends(get_current_contractor)):
    """Get all deals where contractor is assigned"""
    contractor_id = current_user["id"]
    
    # Find deals where this contractor is assigned to any stage or is the main contractor
    all_deals = await db.deals.find({"status": "active"}, {"_id": 0}).to_list(100)
    
    my_deals = []
    for deal in all_deals:
        is_my_deal = False
        
        # Check if contractor is main contractor
        if deal.get("contractor", {}).get("id") == contractor_id:
            is_my_deal = True
        
        # Check if contractor is assigned to any stage (handle both dict and list)
        stages = deal.get("stages", {})
        if isinstance(stages, dict):
            for stage_data in stages.values():
                if isinstance(stage_data, dict) and stage_data.get("contractor_id") == contractor_id:
                    is_my_deal = True
                    break
        
        if is_my_deal:
            # Get client info
            client = await db.users.find_one({"id": deal.get("user_id")}, {"_id": 0, "name": 1, "email": 1})
            deal["client"] = client
            my_deals.append(deal)
    
    return my_deals

# ==================== STAGE-SPECIFIC MESSAGES API ====================

@router.get("/deals/{deal_id}/stages/{stage_key}/messages")
async def get_stage_messages(deal_id: str, stage_key: str, current_user: dict = Depends(get_current_user)):
    """Get messages for a specific stage of a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Get messages for this stage
    messages = await db.deal_messages.find(
        {"deal_id": deal_id, "stage_key": stage_key},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark messages as read by client
    await db.deal_messages.update_many(
        {"deal_id": deal_id, "stage_key": stage_key, "sender_type": "contractor"},
        {"$set": {"read_by_client": True}}
    )
    
    return messages

@router.post("/deals/{deal_id}/stages/{stage_key}/messages")
async def send_stage_message(deal_id: str, stage_key: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Send a message in a stage-specific chat"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Get stage contractor info
    stage_data = deal.get("stages", {}).get(stage_key, {})
    contractor_id = stage_data.get("contractor_id")
    
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "deal_id": deal_id,
        "stage_key": stage_key,
        "sender_id": current_user["id"],
        "sender_name": current_user.get("name", current_user.get("email", "Клиент")),
        "sender_type": "client",
        "recipient_contractor_id": contractor_id,
        "content": data.get("content", ""),
        "file_ids": data.get("file_ids", []),
        "read_by_client": True,
        "read_by_contractor": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_messages.insert_one(message)
    
    # Create notification for contractor
    if contractor_id:
        await db.contractor_notifications.insert_one({
            "id": str(uuid.uuid4()),
            "contractor_id": contractor_id,
            "type": "new_message",
            "title": "Новое сообщение",
            "message": f"Новое сообщение от клиента по сделке",
            "deal_id": deal_id,
            "stage_key": stage_key,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Send Telegram notification to contractor
        contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0, "telegram_chat_id": 1})
        if contractor and contractor.get("telegram_chat_id"):
            car_info = deal.get("car_info", {})
            car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}"
            stage_label = telegram_service.STAGE_LABELS.get(stage_key, stage_key)
            await telegram_service.notify_new_message(
                contractor["telegram_chat_id"],
                current_user.get("name", "Клиент"),
                car_name,
                stage_label,
                data.get("content", ""),
                deal_id,
                stage_key
            )
    
    return {"message": "Сообщение отправлено", "id": message_id}

@router.get("/deals/{deal_id}/stages/{stage_key}/files")
async def get_stage_files(deal_id: str, stage_key: str, current_user: dict = Depends(get_current_user)):
    """Get files for a specific stage of a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    files = await db.deal_files.find(
        {"deal_id": deal_id, "stage_key": stage_key},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return files

@router.post("/deals/{deal_id}/stages/{stage_key}/files")
async def upload_stage_file(
    deal_id: str,
    stage_key: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file to a specific stage"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 50MB)")
    
    file_id = str(uuid.uuid4())
    original_name = file.filename
    file_ext = original_name.split('.')[-1] if '.' in original_name else ''
    saved_name = f"{file_id}.{file_ext}" if file_ext else file_id
    
    # Determine category
    mime_type = file.content_type or "application/octet-stream"
    category = "document"
    if mime_type.startswith("image/"):
        category = "photo"
    elif mime_type.startswith("video/"):
        category = "video"
    
    # Save file
    deal_dir = UPLOADS_DIR / deal_id
    deal_dir.mkdir(parents=True, exist_ok=True)
    file_path = deal_dir / saved_name
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    file_doc = {
        "id": file_id,
        "deal_id": deal_id,
        "stage_key": stage_key,
        "original_name": original_name,
        "saved_name": saved_name,
        "mime_type": mime_type,
        "size": len(file_content),
        "category": category,
        "description": description,
        "uploader_id": current_user["id"],
        "uploader_name": current_user.get("name", "Клиент"),
        "uploader_type": "client",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_files.insert_one(file_doc)
    
    return {"message": "Файл загружен", "file_id": file_id}

# Contractor stage-specific endpoints
@router.get("/contractor/deals/{deal_id}/stages/{stage_key}/messages")
async def get_contractor_stage_messages(deal_id: str, stage_key: str, current_user: dict = Depends(get_current_contractor)):
    """Get messages for a specific stage (contractor view) - only for their assigned stages"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if contractor is assigned to this specific stage
    stage_data = deal.get("stages", {}).get(stage_key, {})
    if stage_data.get("contractor_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Вы не назначены на этот этап")
    
    messages = await db.deal_messages.find(
        {"deal_id": deal_id, "stage_key": stage_key},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark messages as read by contractor
    await db.deal_messages.update_many(
        {"deal_id": deal_id, "stage_key": stage_key, "sender_type": "client"},
        {"$set": {"read_by_contractor": True}}
    )
    
    return messages

@router.post("/contractor/deals/{deal_id}/stages/{stage_key}/messages")
async def send_contractor_stage_message(deal_id: str, stage_key: str, data: dict, current_user: dict = Depends(get_current_contractor)):
    """Send a message in a stage-specific chat (contractor) - only for their assigned stages"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if contractor is assigned to this specific stage
    stage_data = deal.get("stages", {}).get(stage_key, {})
    if stage_data.get("contractor_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Вы не назначены на этот этап")
    
    client_id = deal.get("user_id")
    
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "deal_id": deal_id,
        "stage_key": stage_key,
        "sender_id": current_user["id"],
        "sender_name": current_user.get("company_name", "Подрядчик"),
        "sender_type": "contractor",
        "recipient_client_id": client_id,
        "content": data.get("content", ""),
        "file_ids": data.get("file_ids", []),
        "read_by_client": False,
        "read_by_contractor": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_messages.insert_one(message)
    
    # Create notification for client
    if client_id:
        await db.user_notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": client_id,
            "type": "new_message",
            "title": "Новое сообщение от подрядчика",
            "message": f"Сообщение по этапу сделки",
            "deal_id": deal_id,
            "stage_key": stage_key,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Send Telegram notification to client
        user = await db.users.find_one({"id": client_id}, {"_id": 0, "telegram_chat_id": 1})
        if user and user.get("telegram_chat_id"):
            car_info = deal.get("car_info", {})
            car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}"
            stage_label = telegram_service.STAGE_LABELS.get(stage_key, stage_key)
            await telegram_service.notify_new_message(
                user["telegram_chat_id"],
                current_user.get("company_name", "Подрядчик"),
                car_name,
                stage_label,
                data.get("content", ""),
                deal_id,
                stage_key
            )
    
    return {"message": "Сообщение отправлено", "id": message_id}

@router.post("/contractor/deals/{deal_id}/stages/{stage_key}/files")
async def upload_contractor_stage_file(
    deal_id: str,
    stage_key: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_contractor)
):
    """Upload a file to a specific stage (contractor) - only for their assigned stages"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if contractor is assigned to this specific stage
    stage_data = deal.get("stages", {}).get(stage_key, {})
    if stage_data.get("contractor_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Вы не назначены на этот этап")
    
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 50MB)")
    
    file_id = str(uuid.uuid4())
    original_name = file.filename
    file_ext = original_name.split('.')[-1] if '.' in original_name else ''
    saved_name = f"{file_id}.{file_ext}" if file_ext else file_id
    
    # Determine category
    mime_type = file.content_type or "application/octet-stream"
    category = "document"
    if mime_type.startswith("image/"):
        category = "photo"
    elif mime_type.startswith("video/"):
        category = "video"
    
    # Save file
    deal_dir = UPLOADS_DIR / deal_id
    deal_dir.mkdir(parents=True, exist_ok=True)
    file_path = deal_dir / saved_name
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    file_doc = {
        "id": file_id,
        "deal_id": deal_id,
        "stage_key": stage_key,
        "original_name": original_name,
        "saved_name": saved_name,
        "mime_type": mime_type,
        "size": len(file_content),
        "category": category,
        "description": description,
        "uploader_id": current_user["id"],
        "uploader_name": current_user.get("company_name", "Подрядчик"),
        "uploader_type": "contractor",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deal_files.insert_one(file_doc)
    
    return {"message": "Файл загружен", "file_id": file_id}

# Get contractor's assigned stages for a deal
@router.get("/contractor/deals/{deal_id}/my-stages")
async def get_contractor_my_stages(deal_id: str, current_user: dict = Depends(get_current_contractor)):
    """Get stages assigned to the current contractor for a specific deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    my_stages = []
    stages = deal.get("stages", {})
    for stage_key, stage_data in stages.items():
        if stage_data.get("contractor_id") == current_user["id"]:
            my_stages.append({
                "stage_key": stage_key,
                "status": stage_data.get("status", "pending"),
                "price": stage_data.get("price"),
                "assigned_at": stage_data.get("assigned_at")
            })
    
    return my_stages

# Get unread message counts
@router.get("/deals/{deal_id}/unread-counts")
async def get_deal_unread_counts(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Get unread message counts per stage for a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Count unread messages per stage from contractors
    pipeline = [
        {"$match": {"deal_id": deal_id, "sender_type": "contractor", "read_by_client": {"$ne": True}}},
        {"$group": {"_id": "$stage_key", "count": {"$sum": 1}}}
    ]
    
    results = await db.deal_messages.aggregate(pipeline).to_list(100)
    
    unread_counts = {}
    for r in results:
        if r["_id"]:
            unread_counts[r["_id"]] = r["count"]
    
    return unread_counts

@router.get("/contractor/deals/{deal_id}/unread-counts")
async def get_contractor_deal_unread_counts(deal_id: str, current_user: dict = Depends(get_current_contractor)):
    """Get unread message counts per stage for contractor"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Get contractor's stages
    my_stage_keys = []
    stages = deal.get("stages", {})
    for stage_key, stage_data in stages.items():
        if stage_data.get("contractor_id") == current_user["id"]:
            my_stage_keys.append(stage_key)
    
    if not my_stage_keys:
        return {}
    
    # Count unread messages from client
    pipeline = [
        {"$match": {"deal_id": deal_id, "stage_key": {"$in": my_stage_keys}, "sender_type": "client", "read_by_contractor": {"$ne": True}}},
        {"$group": {"_id": "$stage_key", "count": {"$sum": 1}}}
    ]
    
    results = await db.deal_messages.aggregate(pipeline).to_list(100)
    
    unread_counts = {}
    for r in results:
        if r["_id"]:
            unread_counts[r["_id"]] = r["count"]
    
    return unread_counts

# Stage completion by client (send to moderator review)
@router.post("/deals/{deal_id}/stages/{stage_key}/complete")
async def complete_stage_for_review(deal_id: str, stage_key: str, current_user: dict = Depends(get_current_user)):
    """Mark a stage as complete and send to moderator for review"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    if deal.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сделке")
    
    # Get stage data
    stage_data = deal.get("stages", {}).get(stage_key, {})
    if not stage_data:
        raise HTTPException(status_code=400, detail="Этап не найден")
    
    if not stage_data.get("contractor_id"):
        raise HTTPException(status_code=400, detail="Подрядчик не назначен на этот этап")
    
    if stage_data.get("status") in ["completed", "paid"]:
        raise HTTPException(status_code=400, detail="Этап уже завершён")
    
    if stage_data.get("status") == "pending_review":
        raise HTTPException(status_code=400, detail="Этап уже отправлен на проверку")
    
    # Update stage status to pending_review
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage_key}.status": "pending_review",
                f"stages.{stage_key}.review_requested_at": datetime.now(timezone.utc).isoformat(),
                f"stages.{stage_key}.review_requested_by": current_user["id"]
            }
        }
    )
    
    # Get stage label for notification
    stage_labels = {
        "leasing": "Лизинг",
        "inspection": "Инспекция",
        "export": "Выкуп",
        "logistics_china": "Доставка (Китай)",
        "insurance": "Страхование",
        "delivery_rb": "Доставка (РБ)",
        "customs": "Таможня",
        "completion": "Завершение"
    }
    
    # Notify moderators (create notification in admin notifications or similar)
    car_info = deal.get("car_info", {})
    car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "Авто"
    
    # Send Telegram notification to contractor about pending review
    contractor_id = stage_data.get("contractor_id")
    contractor_name = stage_data.get("contractor_name", "")
    if contractor_id:
        contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0, "telegram_chat_id": 1, "company_name": 1})
        if contractor:
            contractor_name = contractor.get("company_name", contractor_name)
            if contractor.get("telegram_chat_id"):
                await telegram_service.notify_stage_status_change(
                    contractor["telegram_chat_id"],
                    car_name,
                    stage_key,
                    "pending_review",
                    None
                )
    
    # Send Telegram notification to moderators
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            client_name = current_user.get("name", "Клиент")
            await telegram_service.notify_moderators_stage_review(
                moderator_chat_ids,
                client_name,
                car_name,
                stage_key,
                contractor_name,
                deal_id
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
    return {"message": "Этап отправлен на проверку модератору"}

# ==================== END STAGE-SPECIFIC MESSAGES API ====================

# ==================== END DEAL MESSAGES & FILES API ====================

@router.delete("/deals/{deal_id}")
async def cancel_deal(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel a deal and return car to garage"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if deal is not completed
    if deal.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Нельзя отменить завершённую сделку")
    
    # Check if any payments were made
    total_paid = deal.get("total_paid", 0)
    if total_paid > 0:
        raise HTTPException(status_code=400, detail=f"Нельзя отменить сделку с оплаченными этапами (оплачено: ${total_paid})")
    
    # Update car status back to "in_garage"
    car_id = deal.get("car_id")
    if car_id:
        await db.garage.update_one(
            {"id": car_id},
            {"$set": {"status": "in_garage"}}
        )
    
    # Delete the deal
    await db.deals.delete_one({"id": deal_id})
    
    return {"message": "Сделка отменена, авто возвращено в гараж"}

@router.post("/consultant/request")
async def request_consultant_help(data: dict, current_user: dict = Depends(get_current_user)):
    """Request consultant help ($200)"""
    context = data.get("context", "general")  # general, car, deal
    car_id = data.get("car_id")
    deal_id = data.get("deal_id")
    message = data.get("message", "")
    
    # Get account balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < CONSULTANT_FEE:
        raise HTTPException(status_code=400, detail=f"Недостаточно средств. Необходимо ${CONSULTANT_FEE}, баланс: ${balance}")
    
    # Deduct fee
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -CONSULTANT_FEE}}
    )
    
    # Create consultant request
    request_id = str(uuid.uuid4())
    await db.consultant_requests.insert_one({
        "id": request_id,
        "user_id": current_user["id"],
        "context": context,
        "car_id": car_id,
        "deal_id": deal_id,
        "message": message,
        "status": "pending",
        "fee": CONSULTANT_FEE,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Log transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "consultant_fee",
        "amount": -CONSULTANT_FEE,
        "description": "Помощь консультанта",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": "Запрос отправлен. Консультант свяжется с вами в ближайшее время.",
        "request_id": request_id,
        "fee_charged": CONSULTANT_FEE
    }

@router.post("/legal-help/request")
async def request_legal_help(data: dict, current_user: dict = Depends(get_current_user)):
    """Request legal assistance in Belarus or China"""
    country = data.get("country")
    if country not in ["belarus", "china"]:
        raise HTTPException(status_code=400, detail="Выберите страну: belarus или china")
    
    request_id = str(uuid.uuid4())
    
    legal_request = {
        "id": request_id,
        "user_id": current_user["id"],
        "user_email": current_user.get("email"),
        "user_name": current_user.get("name"),
        "country": country,
        "country_name": "Беларусь" if country == "belarus" else "Китай",
        "status": "pending",  # pending, in_progress, completed
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.legal_requests.insert_one(legal_request)
    
    return {
        "message": f"Запрос на юридическую помощь в {'Беларуси' if country == 'belarus' else 'Китае'} отправлен",
        "request_id": request_id
    }

@router.get("/legal-help/requests")
async def get_legal_help_requests(current_user: dict = Depends(get_current_user)):
    """Get user's legal help requests"""
    requests = await db.legal_requests.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return requests

