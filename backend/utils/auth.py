"""Authentication utilities"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from typing import List

import sys
sys.path.insert(0, '/app/backend')

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS
from database import db

# Password hashing
# Suppress bcrypt version warning from passlib (passlib 1.7.4 incompatibility with bcrypt 4.x)
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer security
security = HTTPBearer()

# Admin emails
ADMIN_EMAILS = ["votin@tut.by", "admin@carbridge.by"]


def create_token(user_id: str, email: str, token_type: str = "user") -> str:
    """Create JWT token for user or contractor"""
    expiration = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {"sub": user_id, "email": email, "exp": expiration}
    if token_type == "contractor":
        payload["type"] = "contractor"
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_contractor(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current contractor from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "contractor":
            raise HTTPException(status_code=403, detail="Доступ только для подрядчиков")
        
        contractor = await db.contractors.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not contractor:
            raise HTTPException(status_code=401, detail="Contractor not found")
        return contractor
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")


def require_role(allowed_roles: List[str]):
    """Dependency to require specific user roles"""
    async def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            
            user_role = user.get("role", "user")
            if user_role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    return role_checker
