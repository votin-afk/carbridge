"""Affiliate Program routes"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid
import hashlib

import sys
sys.path.insert(0, '/app/backend')

from database import db
from utils.auth import get_current_user


router = APIRouter(prefix="/affiliate", tags=["affiliate"])


# ==================== CONSTANTS ====================
COMMISSION_RATE = 0.03  # 3% platform commission
AFFILIATE_SHARE = 0.20  # 20% of commission goes to affiliate
PARTNER_THRESHOLD = 3   # 3 completed deals to become partner


# ==================== MODELS ====================

class AffiliateRegister(BaseModel):
    phone: Optional[str] = None
    telegram: Optional[str] = None
    payment_method: str = "platform_balance"
    bank_details: Optional[str] = None


class AffiliateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    user_email: str
    user_name: str
    referral_code: str
    referral_link: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    payment_method: str
    bank_details: Optional[str] = None
    is_partner: bool = False
    total_referrals: int = 0
    active_referrals: int = 0
    completed_deals: int = 0
    total_earnings: float = 0.0
    pending_earnings: float = 0.0
    withdrawn_earnings: float = 0.0
    available_balance: float = 0.0
    created_at: str


class WithdrawRequest(BaseModel):
    amount: float
    method: str  # bank, card, crypto, platform_balance
    details: Optional[str] = None


# ==================== HELPERS ====================

def generate_referral_code(user_id: str) -> str:
    """Generate unique referral code from user id"""
    hash_obj = hashlib.md5(user_id.encode())
    return f"CB{hash_obj.hexdigest()[:8].upper()}"


# ==================== ENDPOINTS ====================

@router.post("/register", response_model=AffiliateResponse)
async def register_as_affiliate(data: AffiliateRegister, current_user: dict = Depends(get_current_user)):
    """Register user in affiliate program"""
    existing = await db.affiliates.find_one({"user_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже зарегистрированы в партнёрской программе")
    
    referral_code = generate_referral_code(current_user["id"])
    
    affiliate_doc = {
        "user_id": current_user["id"],
        "user_email": current_user["email"],
        "user_name": current_user.get("name", ""),
        "referral_code": referral_code,
        "phone": data.phone,
        "telegram": data.telegram,
        "payment_method": data.payment_method,
        "bank_details": data.bank_details,
        "is_partner": False,
        "total_referrals": 0,
        "active_referrals": 0,
        "completed_deals": 0,
        "total_earnings": 0.0,
        "pending_earnings": 0.0,
        "withdrawn_earnings": 0.0,
        "available_balance": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.affiliates.insert_one(affiliate_doc)
    affiliate_doc.pop("_id", None)
    affiliate_doc["referral_link"] = f"https://carbridge.by/?ref={referral_code}"
    
    return AffiliateResponse(**affiliate_doc)


@router.get("/status")
async def get_affiliate_status(current_user: dict = Depends(get_current_user)):
    """Get current user's affiliate status with detailed stats"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    referrals = await db.referrals.find(
        {"affiliate_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    
    total_referrals = len(referrals)
    total_completed_deals = sum(r.get("completed_deals", 0) for r in referrals)
    total_commission_earned = sum(r.get("total_commission", 0) for r in referrals)
    
    affiliate["referral_link"] = f"https://carbridge.by/?ref={affiliate['referral_code']}"
    affiliate["stats"] = {
        "total_referrals": total_referrals,
        "completed_referral_deals": total_completed_deals,
        "total_commission_earned": total_commission_earned,
        "commission_rate": f"{AFFILIATE_SHARE * 100:.0f}% от комиссии платформы ({COMMISSION_RATE * 100:.0f}%)"
    }
    
    return affiliate


@router.get("/referrals")
async def get_referrals(current_user: dict = Depends(get_current_user)):
    """Get list of referrals for current affiliate"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    referrals = await db.referrals.find(
        {"affiliate_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    
    return referrals


@router.get("/transactions")
async def get_affiliate_transactions(current_user: dict = Depends(get_current_user)):
    """Get affiliate's transaction history"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    transactions = await db.affiliate_transactions.find(
        {"affiliate_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transactions


@router.post("/withdraw")
async def withdraw_affiliate_earnings(request: WithdrawRequest, current_user: dict = Depends(get_current_user)):
    """Withdraw affiliate earnings"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть положительной")
    
    if request.amount > affiliate.get("available_balance", 0):
        raise HTTPException(status_code=400, detail="Недостаточно средств для вывода")
    
    withdrawal_id = str(uuid.uuid4())
    withdrawal_doc = {
        "id": withdrawal_id,
        "affiliate_id": current_user["id"],
        "amount": request.amount,
        "method": request.method,
        "details": request.details,
        "status": "pending" if request.method != "platform_balance" else "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    if request.method == "platform_balance":
        await db.accounts.update_one(
            {"user_id": current_user["id"]},
            {"$inc": {"balance": request.amount}},
            upsert=True
        )
        withdrawal_doc["status"] = "completed"
        withdrawal_doc["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.affiliate_withdrawals.insert_one(withdrawal_doc)
    
    await db.affiliates.update_one(
        {"user_id": current_user["id"]},
        {
            "$inc": {
                "available_balance": -request.amount,
                "withdrawn_earnings": request.amount
            }
        }
    )
    
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "affiliate_id": current_user["id"],
        "type": "withdrawal",
        "amount": -request.amount,
        "method": request.method,
        "description": f"Вывод средств ({request.method})",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.affiliate_transactions.insert_one(transaction_doc)
    
    return {
        "message": "Заявка на вывод создана" if request.method != "platform_balance" else "Средства переведены на баланс платформы",
        "withdrawal_id": withdrawal_id,
        "amount": request.amount,
        "method": request.method,
        "status": withdrawal_doc["status"]
    }


@router.post("/register-referral")
async def register_referral(referral_code: str, current_user: dict = Depends(get_current_user)):
    """Register a user as referral"""
    affiliate = await db.affiliates.find_one({"referral_code": referral_code})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Неверный реферальный код")
    
    if affiliate["user_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Нельзя использовать собственный реферальный код")
    
    existing = await db.referrals.find_one({"referral_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже зарегистрированы как реферал")
    
    referral_doc = {
        "id": str(uuid.uuid4()),
        "affiliate_id": affiliate["user_id"],
        "referral_id": current_user["id"],
        "referral_email": current_user["email"],
        "referral_name": current_user.get("name", ""),
        "completed_deals": 0,
        "total_commission": 0.0,
        "registered_at": datetime.now(timezone.utc).isoformat()
    }
    await db.referrals.insert_one(referral_doc)
    
    await db.affiliates.update_one(
        {"user_id": affiliate["user_id"]},
        {"$inc": {"total_referrals": 1, "active_referrals": 1}}
    )
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"referred_by": affiliate["user_id"], "referral_code_used": referral_code}}
    )
    
    return {"message": "Реферальный код применён", "affiliate_name": affiliate.get("user_name", "")}


@router.post("/record-commission")
async def record_affiliate_commission(
    referral_user_id: str,
    deal_amount: float,
    deal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Record commission for affiliate when referral completes a deal"""
    referral = await db.referrals.find_one({"referral_id": referral_user_id})
    if not referral:
        return {"message": "User is not a referral"}
    
    affiliate_id = referral["affiliate_id"]
    platform_commission = deal_amount * COMMISSION_RATE
    affiliate_commission = platform_commission * AFFILIATE_SHARE
    
    await db.referrals.update_one(
        {"referral_id": referral_user_id},
        {
            "$inc": {
                "completed_deals": 1,
                "total_commission": affiliate_commission
            }
        }
    )
    
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
    
    if update_result and update_result.get("completed_deals", 0) >= PARTNER_THRESHOLD and not update_result.get("is_partner"):
        await db.affiliates.update_one(
            {"user_id": affiliate_id},
            {"$set": {"is_partner": True, "partner_since": datetime.now(timezone.utc).isoformat()}}
        )
    
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "affiliate_id": affiliate_id,
        "type": "commission",
        "amount": affiliate_commission,
        "deal_id": deal_id,
        "referral_id": referral_user_id,
        "description": f"Комиссия со сделки #{deal_id[:8]}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.affiliate_transactions.insert_one(transaction_doc)
    
    return {
        "message": "Commission recorded",
        "affiliate_commission": affiliate_commission,
        "is_partner": update_result.get("is_partner", False) if update_result else False
    }


@router.get("/check/{referral_code}")
async def check_referral_code(referral_code: str):
    """Check if referral code is valid (public endpoint)"""
    affiliate = await db.affiliates.find_one({"referral_code": referral_code}, {"_id": 0, "user_name": 1, "is_partner": 1})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")
    
    return {
        "valid": True,
        "affiliate_name": affiliate.get("user_name", "Партнёр CarBridge"),
        "is_partner": affiliate.get("is_partner", False)
    }
