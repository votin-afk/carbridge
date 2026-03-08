"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid

import sys
sys.path.insert(0, '/app/backend')

from database import db
from utils.auth import (
    create_token, verify_password, hash_password, 
    get_current_user, ADMIN_EMAILS
)


router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    user_type: Literal["individual", "legal"] = "individual"
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    user_type: str
    role: str = "user"
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== ENDPOINTS ====================

@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    """Register a new user"""
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine role - admin emails get admin role automatically
    role = "admin" if user.email in ADMIN_EMAILS else "user"
    
    # Check referral code if provided
    referred_by = None
    referral_code_used = None
    if user.referral_code:
        affiliate = await db.affiliates.find_one({"referral_code": user.referral_code})
        if affiliate:
            referred_by = affiliate["user_id"]
            referral_code_used = user.referral_code
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "user_type": user.user_type,
        "role": role,
        "referred_by": referred_by,
        "referral_code_used": referral_code_used,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # If referral code was valid, create referral record
    if referred_by:
        referral_doc = {
            "id": str(uuid.uuid4()),
            "affiliate_id": referred_by,
            "referral_id": user_id,
            "referral_email": user.email,
            "referral_name": user.name,
            "completed_deals": 0,
            "total_commission": 0.0,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        await db.referrals.insert_one(referral_doc)
        
        # Update affiliate stats
        await db.affiliates.update_one(
            {"user_id": referred_by},
            {"$inc": {"total_referrals": 1, "active_referrals": 1}}
        )
    
    token = create_token(user_id, user.email)
    user_response = UserResponse(
        id=user_id, email=user.email, name=user.name,
        phone=user.phone, user_type=user.user_type, role=role, created_at=user_doc["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update role for admin emails if not already set
    role = user.get("role", "user")
    if credentials.email in ADMIN_EMAILS and role != "admin":
        role = "admin"
        await db.users.update_one({"email": credentials.email}, {"$set": {"role": "admin"}})
    
    token = create_token(user["id"], user["email"])
    user_response = UserResponse(
        id=user["id"], email=user["email"], name=user["name"],
        phone=user.get("phone"), user_type=user["user_type"], role=role, created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user["id"], email=current_user["email"], name=current_user["name"],
        phone=current_user.get("phone"), user_type=current_user["user_type"],
        role=current_user.get("role", "user"), created_at=current_user["created_at"]
    )
