"""User account and related routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

import sys
sys.path.insert(0, '/app/backend')

from database import db
from utils.auth import get_current_user


router = APIRouter(tags=["user"])


# ==================== USER ENDPOINTS ====================

@router.get("/user/role")
async def get_user_role(current_user: dict = Depends(get_current_user)):
    """Get current user's role"""
    return {"role": current_user.get("role", "user")}


@router.get("/user/account")
async def get_user_account(current_user: dict = Depends(get_current_user)):
    """Get user account details including balance, verification status, and contract status"""
    account = await db.accounts.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    if not account:
        account = {
            "user_id": current_user["id"],
            "balance": 0.0,
            "is_verified": False,
            "contract_signed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.accounts.insert_one(account)
        account.pop("_id", None)
    
    return {
        "balance": account.get("balance", 0.0),
        "is_verified": account.get("is_verified", False),
        "contract_signed": account.get("contract_signed", False)
    }


@router.post("/user/account/deposit")
async def deposit_to_account(amount: float, current_user: dict = Depends(get_current_user)):
    """Deposit funds to user account"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": amount}},
        upsert=True
    )
    
    return {"message": f"Successfully deposited ${amount}", "new_balance": amount}


@router.get("/account/summary")
async def get_account_summary(current_user: dict = Depends(get_current_user)):
    """Get account summary for dashboard"""
    account = await db.accounts.find_one({"user_id": current_user["id"]}, {"_id": 0})
    verification = await db.verifications.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    active_deal = await db.deals.find_one(
        {"user_id": current_user["id"], "status": "active"},
        {"_id": 0}
    )
    
    return {
        "balance": account.get("balance", 0) if account else 0,
        "is_verified": account.get("is_verified", False) if account else False,
        "verification_status": verification.get("status") if verification else "not_started",
        "contract_signed": verification.get("contract_signed", False) if verification else False,
        "contract_number": verification.get("contract_number") if verification else None,
        "active_deal": active_deal
    }


# ==================== LEGAL HELP ENDPOINTS ====================

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
        "status": "pending",
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


# ==================== CONSULTANT HELP ====================

CONSULTANT_COST = 200  # USD

@router.post("/consultant/request")
async def request_consultant_help(data: dict, current_user: dict = Depends(get_current_user)):
    """Request consultant help for car selection"""
    car_id = data.get("car_id")
    deal_id = data.get("deal_id")
    request_type = data.get("type", "selection")  # selection, negotiation, inspection
    
    # Check user balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < CONSULTANT_COST:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно средств. Требуется ${CONSULTANT_COST}, на балансе ${balance}"
        )
    
    # Deduct from balance
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -CONSULTANT_COST}}
    )
    
    request_id = str(uuid.uuid4())
    help_request = {
        "id": request_id,
        "user_id": current_user["id"],
        "car_id": car_id,
        "deal_id": deal_id,
        "type": request_type,
        "cost": CONSULTANT_COST,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.help_requests.insert_one(help_request)
    
    return {
        "message": "Запрос на помощь консультанта отправлен",
        "request_id": request_id,
        "cost": CONSULTANT_COST,
        "new_balance": balance - CONSULTANT_COST
    }
