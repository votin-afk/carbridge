from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import httpx
from bs4 import BeautifulSoup
import re
import asyncio
from io import BytesIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'carbridge_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ==================== PRO-AUCTIONS PARSER CONFIG ====================
PRO_AUCTIONS_BASE_URL = "https://demo.pro-auctions.ru/china-used/"
CACHE_TTL_SECONDS = 300  # 5 minutes cache

# ==================== CHE168 API CONFIG ====================
CHE168_API_BASE_URL = "https://api1.auto-api.com/api/v2/che168"
CHE168_API_KEY = "DQugK90Bo5ci1ZeDP6Wr"

# Simple in-memory cache
_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, datetime] = {}

def get_cached(key: str) -> Optional[Any]:
    """Get cached value if not expired"""
    if key in _cache and key in _cache_timestamps:
        if datetime.now(timezone.utc) - _cache_timestamps[key] < timedelta(seconds=CACHE_TTL_SECONDS):
            return _cache[key]
    return None

def set_cache(key: str, value: Any):
    """Set cache value with timestamp"""
    _cache[key] = value
    _cache_timestamps[key] = datetime.now(timezone.utc)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

# User roles
ROLES = ["user", "moderator", "admin"]

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    user_type: Literal["individual", "legal"] = "individual"

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

class CarCreate(BaseModel):
    brand: str
    model: str
    year: int
    price_cny: float
    engine_type: Literal["ice", "hybrid", "electric"]
    engine_volume: Optional[int] = None
    mileage: Optional[int] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    calculated_price_usd: Optional[float] = None
    calculated_price_byn: Optional[float] = None

class CarResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    brand: str
    model: str
    year: int
    price_cny: float
    engine_type: str
    engine_volume: Optional[int] = None
    mileage: Optional[int] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    calculated_price_usd: Optional[float] = None
    calculated_price_byn: Optional[float] = None
    contractors: Optional[dict] = None
    notes: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None

class TenderCreate(BaseModel):
    car_id: str

class TenderOfferCreate(BaseModel):
    tender_id: str
    price_usd: float
    delivery_days: int
    delivery_cost: float
    payment_method: str
    contractor_name: str
    contractor_rating: float
    notes: Optional[str] = None

class TenderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    car_id: Optional[str] = None
    car_info: Optional[dict] = None
    status: str
    offers: List[dict] = []
    selected_offer_id: Optional[str] = None
    deal_created: Optional[bool] = False
    created_at: str

class DocumentCreate(BaseModel):
    title: str
    doc_type: str
    file_url: str
    car_id: Optional[str] = None
    tender_id: Optional[str] = None

class DocumentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    doc_type: str
    file_url: str
    car_id: Optional[str] = None
    tender_id: Optional[str] = None
    created_at: str

# ==================== CONTRACTOR MODELS ====================

class ContractorCreate(BaseModel):
    name: str
    contractor_type: Literal["inspection", "export", "logistics"]
    description: str
    services: str
    price_range: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    wechat: Optional[str] = None
    telegram: Optional[str] = None
    rating: float = 5.0
    deals_count: int = 0
    is_verified: bool = False
    logo_url: Optional[str] = None

class ContractorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: Optional[str] = None
    company_name: Optional[str] = None
    contractor_type: Optional[str] = None
    description: Optional[str] = None
    services: Any = None  # Can be string or list
    service_prices: Optional[dict] = None  # {service_name: price_usd}
    price_range: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    wechat: Optional[str] = None
    telegram: Optional[str] = None
    rating: Optional[float] = 5.0
    deals_count: Optional[int] = 0
    is_verified: Optional[bool] = False
    verified: Optional[bool] = False
    country: Optional[str] = None
    contact_person: Optional[str] = None
    is_verified: bool
    logo_url: Optional[str] = None
    created_at: str

class ContractorAssignment(BaseModel):
    car_id: str
    contractor_id: str
    stage: Literal["inspection", "export", "logistics", "leasing"]

# ==================== AFFILIATE PROGRAM MODELS ====================

class AffiliateRegister(BaseModel):
    phone: Optional[str] = None
    telegram: Optional[str] = None
    payment_method: Literal["bank_transfer", "crypto", "platform_balance"] = "platform_balance"
    bank_details: Optional[str] = None

class AffiliateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    referral_code: str
    referral_link: str
    is_partner: bool  # True after 3 completed referral deals
    total_referrals: int
    active_referrals: int
    completed_deals: int
    total_earnings: float
    pending_earnings: float
    withdrawn_earnings: float
    available_balance: float
    created_at: str

class ReferralStats(BaseModel):
    referral_id: str
    referral_email: str
    referral_name: str
    registered_at: str
    completed_deals: int
    total_commission: float

class WithdrawRequest(BaseModel):
    amount: float
    method: Literal["bank_transfer", "crypto", "platform_balance"]
    details: Optional[str] = None

class CalculatorInput(BaseModel):
    price_cny: float
    age: Literal["under3", "3to5", "over5"]
    engine_type: Literal["ice", "hybrid", "electric"]
    engine_volume: Optional[int] = None
    user_type: Literal["individual", "legal"] = "individual"
    use_decree_140: bool = False
    payment_via_platform: bool = True  # True = через платформу, False = через банк

class CalculatorResult(BaseModel):
    price_cny: float
    price_eur: float
    price_usd: float
    customs_duty: float
    utilization_fee: float
    vat: float
    fixed_costs_byn: float
    fixed_costs_usd: float
    platform_commission: float  # 3% комиссия платформы
    payment_commission: float  # 1.5% за оплату
    decree_140_discount: float  # Скидка по Указу 140
    total_byn: float
    total_usd: float
    breakdown: dict

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class ParseUrlRequest(BaseModel):
    url: str

class ParsedCarData(BaseModel):
    success: bool
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price_cny: Optional[float] = None
    engine_type: Optional[str] = None
    engine_volume: Optional[int] = None
    mileage: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: str
    error: Optional[str] = None

class CatalogSearchParams(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    engine_type: Optional[str] = None
    body_type: Optional[str] = None
    query: Optional[str] = None
    page: int = 1
    limit: int = 20

class CatalogCarModel(BaseModel):
    id: str
    brand: str
    brand_cn: str = ""
    model: str
    model_cn: str = ""
    year_from: int
    year_to: Optional[int] = None
    price_from_cny: float
    price_to_cny: Optional[float] = None
    engine_type: str
    engine_volume: Optional[int] = None
    body_type: str
    image_url: str
    description: str = ""
    features: List[str] = []
    popularity: int = 0
    mileage: Optional[int] = None
    source: Optional[str] = None
    fuel_type: Optional[str] = None
    source_url: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    address: Optional[str] = None
    vin: Optional[str] = None
    power: Optional[int] = None

class CatalogSearchResult(BaseModel):
    cars: List[CatalogCarModel]
    total: int
    page: int
    pages: int
    search_links: dict

# ==================== HOT DEALS MODELS ====================

class HotDealCreate(BaseModel):
    brand: str
    model: str
    year: int
    price_cny: float
    special_price_cny: Optional[float] = None  # Специальная цена (если есть скидка)
    mileage: Optional[int] = None
    engine_type: Literal["ice", "hybrid", "electric"] = "ice"
    engine_volume: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    expires_at: str  # ISO datetime when deal expires
    contact_info: Optional[str] = None

class HotDealResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    brand: str
    model: str
    year: int
    price_cny: float
    special_price_cny: Optional[float] = None
    calculated_price_usd: Optional[float] = None
    mileage: Optional[int] = None
    engine_type: str
    engine_volume: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    expires_at: str
    seller_id: str
    seller_name: str
    seller_type: str  # "moderator" or "contractor"
    is_verified_seller: bool = False
    created_at: str

# ==================== CHINESE CAR CATALOG DATA ====================

CHINESE_CAR_CATALOG = [
    # BYD
    {
        "id": "byd-han-ev",
        "brand": "BYD", "brand_cn": "比亚迪",
        "model": "Han EV", "model_cn": "汉EV",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 180000, "price_to_cny": 330000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Флагманский электрический седан BYD с батареей Blade. Запас хода до 605 км.",
        "features": ["Blade Battery", "DiPilot", "605 км запас хода", "0-100 за 3.9с"],
        "popularity": 95
    },
    {
        "id": "byd-seal",
        "brand": "BYD", "brand_cn": "比亚迪",
        "model": "Seal", "model_cn": "海豹",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 189800, "price_to_cny": 289800,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Спортивный электроседан на платформе e-platform 3.0. Конкурент Tesla Model 3.",
        "features": ["e-platform 3.0", "CTB технология", "700 км запас хода", "AWD"],
        "popularity": 90
    },
    {
        "id": "byd-song-plus-dmi",
        "brand": "BYD", "brand_cn": "比亚迪",
        "model": "Song Plus DM-i", "model_cn": "宋PLUS DM-i",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 150000, "price_to_cny": 220000,
        "engine_type": "hybrid", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Популярный гибридный кроссовер с системой DM-i. Расход 3.8л/100км.",
        "features": ["DM-i гибрид", "1100 км запас хода", "Расход 3.8л", "DiLink 4.0"],
        "popularity": 92
    },
    {
        "id": "byd-dolphin",
        "brand": "BYD", "brand_cn": "比亚迪",
        "model": "Dolphin", "model_cn": "海豚",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 96800, "price_to_cny": 136800,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "hatchback",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Компактный городской электромобиль. Идеален для города.",
        "features": ["e-platform 3.0", "401 км запас хода", "Быстрая зарядка", "Компактный"],
        "popularity": 88
    },
    # Li Auto
    {
        "id": "li-l9",
        "brand": "Li Auto", "brand_cn": "理想",
        "model": "L9", "model_cn": "L9",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 429800, "price_to_cny": 469800,
        "engine_type": "hybrid", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.pexels.com/photos/32912506/pexels-photo-32912506.jpeg?w=800",
        "description": "Премиальный 6-местный SUV с увеличенным запасом хода. Флагман Li Auto.",
        "features": ["EREV гибрид", "1315 км запас хода", "6 мест", "AD Max автопилот"],
        "popularity": 94
    },
    {
        "id": "li-l7",
        "brand": "Li Auto", "brand_cn": "理想",
        "model": "L7", "model_cn": "L7",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 319800, "price_to_cny": 379800,
        "engine_type": "hybrid", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Среднеразмерный премиум SUV. 5 мест, богатое оснащение.",
        "features": ["EREV гибрид", "1100 км запас хода", "5 мест", "Air подвеска"],
        "popularity": 91
    },
    {
        "id": "li-mega",
        "brand": "Li Auto", "brand_cn": "理想",
        "model": "MEGA", "model_cn": "MEGA",
        "year_from": 2024, "year_to": 2024,
        "price_from_cny": 559800, "price_to_cny": 559800,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "mpv",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Первый полностью электрический MPV от Li Auto. 5C зарядка.",
        "features": ["800V платформа", "5C зарядка", "710 км запас хода", "7 мест"],
        "popularity": 85
    },
    # NIO
    {
        "id": "nio-et7",
        "brand": "NIO", "brand_cn": "蔚来",
        "model": "ET7", "model_cn": "ET7",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 428000, "price_to_cny": 536000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Флагманский электроседан NIO с твердотельной батареей 150 кВт·ч.",
        "features": ["Замена батарей", "1000 км запас хода", "NAD автопилот", "Твердотельная батарея"],
        "popularity": 89
    },
    {
        "id": "nio-es6",
        "brand": "NIO", "brand_cn": "蔚来",
        "model": "ES6", "model_cn": "ES6",
        "year_from": 2019, "year_to": 2024,
        "price_from_cny": 338000, "price_to_cny": 426000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Популярный электрический SUV от NIO с возможностью замены батарей.",
        "features": ["Замена батарей", "610 км запас хода", "NOMI AI", "Air подвеска"],
        "popularity": 87
    },
    # Zeekr
    {
        "id": "zeekr-001",
        "brand": "Zeekr", "brand_cn": "极氪",
        "model": "001", "model_cn": "001",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 269000, "price_to_cny": 389000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "shooting_brake",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Стильный электрический shooting brake от Geely. Платформа SEA.",
        "features": ["SEA платформа", "1000 км запас хода", "0-100 за 3.8с", "Безрамочные двери"],
        "popularity": 86
    },
    {
        "id": "zeekr-009",
        "brand": "Zeekr", "brand_cn": "极氪",
        "model": "009", "model_cn": "009",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 499000, "price_to_cny": 788000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "mpv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Премиальный электрический минивэн. Конкурент Lexus LM.",
        "features": ["140 кВт·ч батарея", "822 км запас хода", "VIP салон", "Air подвеска"],
        "popularity": 82
    },
    # Xpeng
    {
        "id": "xpeng-p7",
        "brand": "Xpeng", "brand_cn": "小鹏",
        "model": "P7", "model_cn": "P7",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 209900, "price_to_cny": 339900,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Спортивный электроседан с продвинутым автопилотом XPILOT.",
        "features": ["XPILOT 4.0", "706 км запас хода", "0-100 за 4.3с", "OTA обновления"],
        "popularity": 84
    },
    {
        "id": "xpeng-g9",
        "brand": "Xpeng", "brand_cn": "小鹏",
        "model": "G9", "model_cn": "G9",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 309900, "price_to_cny": 469900,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Флагманский SUV Xpeng с 800V архитектурой и быстрой зарядкой.",
        "features": ["800V платформа", "702 км запас хода", "5C зарядка", "XPILOT 4.0"],
        "popularity": 83
    },
    # Geely
    {
        "id": "geely-xingyue-l",
        "brand": "Geely", "brand_cn": "吉利",
        "model": "Xingyue L", "model_cn": "星越L",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 137700, "price_to_cny": 182700,
        "engine_type": "ice", "engine_volume": 2000,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Премиальный кроссовер на платформе CMA. Турбо 2.0T.",
        "features": ["CMA платформа", "Volvo технологии", "2.0T двигатель", "Pilot автопилот"],
        "popularity": 80
    },
    # Chery
    {
        "id": "chery-tiggo-8-pro",
        "brand": "Chery", "brand_cn": "奇瑞",
        "model": "Tiggo 8 Pro", "model_cn": "瑞虎8 PRO",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 119900, "price_to_cny": 159900,
        "engine_type": "ice", "engine_volume": 1600,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Семейный 7-местный кроссовер с отличным соотношением цена/качество.",
        "features": ["7 мест", "1.6T двигатель", "Lion 5.0 система", "Просторный салон"],
        "popularity": 78
    },
    # Haval
    {
        "id": "haval-h6",
        "brand": "Haval", "brand_cn": "哈弗",
        "model": "H6", "model_cn": "H6",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 99900, "price_to_cny": 149900,
        "engine_type": "ice", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Бестселлер среди китайских кроссоверов. Надежность и комфорт.",
        "features": ["1.5T/2.0T двигатель", "Lemon платформа", "Богатое оснащение", "Низкая цена"],
        "popularity": 85
    },
    {
        "id": "haval-jolion",
        "brand": "Haval", "brand_cn": "哈弗",
        "model": "Jolion", "model_cn": "初恋",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 79900, "price_to_cny": 119900,
        "engine_type": "ice", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Компактный молодежный кроссовер. Стильный дизайн, доступная цена.",
        "features": ["1.5T двигатель", "Молодежный дизайн", "Богатая комплектация", "Экономичный"],
        "popularity": 79
    },
    # Changan
    {
        "id": "changan-uni-k",
        "brand": "Changan", "brand_cn": "长安",
        "model": "UNI-K", "model_cn": "UNI-K",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 149900, "price_to_cny": 189900,
        "engine_type": "ice", "engine_volume": 2000,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Футуристичный кроссовер с безрамочной решеткой радиатора.",
        "features": ["Blue Core 2.0T", "IMS система", "Футуристичный дизайн", "5/7 мест"],
        "popularity": 77
    },
    # Hongqi
    {
        "id": "hongqi-h9",
        "brand": "Hongqi", "brand_cn": "红旗",
        "model": "H9", "model_cn": "H9",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 309800, "price_to_cny": 539800,
        "engine_type": "ice", "engine_volume": 3000,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Флагманский седан представительского класса. Китайский Maybach.",
        "features": ["V6 3.0T", "Массаж сидений", "Air подвеска", "Премиум аудио"],
        "popularity": 81
    },
    {
        "id": "hongqi-e-hs9",
        "brand": "Hongqi", "brand_cn": "红旗",
        "model": "E-HS9", "model_cn": "E-HS9",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 509800, "price_to_cny": 729800,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Премиальный электрический SUV от Hongqi. Максимальная роскошь.",
        "features": ["120 кВт·ч батарея", "690 км запас хода", "VIP конфигурация", "4/6/7 мест"],
        "popularity": 75
    },
]

# ==================== CHE168 API PARSER ====================

class Che168API:
    """API client for che168.com via auto-api.com"""
    
    BASE_URL = CHE168_API_BASE_URL
    API_KEY = CHE168_API_KEY
    
    @staticmethod
    def map_engine_type(engine_type_ru: str) -> str:
        """Map Russian engine type to internal format"""
        if not engine_type_ru:
            return "ice"
        engine_lower = engine_type_ru.lower()
        if 'электрический' in engine_lower or 'bev' in engine_lower:
            return "electric"
        elif 'гибрид' in engine_lower or 'hybrid' in engine_lower or 'phev' in engine_lower or 'hev' in engine_lower:
            return "hybrid"
        return "ice"
    
    @staticmethod
    def map_body_type(body_type_ru: str) -> str:
        """Map Russian body type to internal format"""
        if not body_type_ru:
            return "sedan"
        body_lower = body_type_ru.lower()
        if 'седан' in body_lower:
            return "sedan"
        elif 'кроссовер' in body_lower or 'внедорожник' in body_lower or 'suv' in body_lower:
            return "suv"
        elif 'хэтчбек' in body_lower or 'хетчбек' in body_lower:
            return "hatchback"
        elif 'минивэн' in body_lower or 'mpv' in body_lower:
            return "mpv"
        elif 'универсал' in body_lower:
            return "wagon"
        elif 'пикап' in body_lower:
            return "pickup"
        elif 'купе' in body_lower or 'родстер' in body_lower:
            return "coupe"
        elif 'малолитражка' in body_lower:
            return "hatchback"
        return "sedan"
    
    @staticmethod
    async def get_filters() -> Dict[str, Any]:
        """Get available filters from API"""
        cache_key = "che168_filters"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{Che168API.BASE_URL}/filters",
                    params={"api_key": Che168API.API_KEY}
                )
                if response.status_code == 200:
                    data = response.json()
                    set_cache(cache_key, data)
                    return data
        except Exception as e:
            logger.error(f"Che168API.get_filters error: {e}")
        return {}
    
    @staticmethod
    async def get_brands() -> List[Dict[str, Any]]:
        """Get list of all brands from Che168"""
        filters = await Che168API.get_filters()
        if not filters or "mark" not in filters:
            return []
        
        brands = []
        for brand_name, brand_data in filters.get("mark", {}).items():
            models = brand_data.get("model", []) if isinstance(brand_data, dict) else []
            brands.append({
                "name": brand_name,
                "slug": brand_name.lower().replace(" ", "-"),
                "count": len(models) * 10,  # Approximate count
                "url": f"https://www.che168.com/china/{brand_name.lower()}/"
            })
        
        # Sort by name
        brands.sort(key=lambda x: x["name"])
        return brands
    
    @staticmethod
    async def get_models(brand: str) -> List[Dict[str, str]]:
        """Get models for a specific brand"""
        filters = await Che168API.get_filters()
        if not filters or "mark" not in filters:
            return []
        
        for brand_name, brand_data in filters.get("mark", {}).items():
            if brand_name.lower() == brand.lower():
                models = brand_data.get("model", []) if isinstance(brand_data, dict) else []
                return [{"name": m, "slug": m.lower().replace(" ", "-"), "count": 10} for m in models]
        
        return []
    
    @staticmethod
    async def search_cars(
        mark: Optional[str] = None,
        model: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        engine_type: Optional[str] = None,
        body_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search cars from Che168 API"""
        cache_key = f"che168_search_{mark}_{model}_{year_from}_{year_to}_{price_from}_{price_to}_{engine_type}_{body_type}_{page}"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                "api_key": Che168API.API_KEY,
                "page": page
            }
            
            if mark:
                params["mark"] = mark
            if model:
                params["model"] = model
            if year_from:
                params["year_from"] = year_from
            if year_to:
                params["year_to"] = year_to
            if price_from:
                params["price_from"] = int(price_from)
            if price_to:
                params["price_to"] = int(price_to)
            if engine_type:
                # Map internal engine type to API format
                engine_map = {
                    "electric": "Электрический (BEV)",
                    "hybrid": "Гибридный (HEV)",
                    "ice": "Бензиновый"
                }
                if engine_type in engine_map:
                    params["engine_type"] = engine_map[engine_type]
            if body_type:
                # Map internal body type to API format
                body_map = {
                    "sedan": "Седан",
                    "suv": "Кроссовер/внедорожник",
                    "hatchback": "Хэтчбек",
                    "mpv": "Минивэн",
                    "wagon": "Универсал",
                    "pickup": "Пикап"
                }
                if body_type in body_map:
                    params["body_type"] = body_map[body_type]
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{Che168API.BASE_URL}/offers",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", [])
                    meta = data.get("meta", {})
                    
                    cars = []
                    for item in result:
                        car_data = item.get("data", {})
                        
                        # Parse images from string or list
                        images = car_data.get("images", [])
                        if isinstance(images, str):
                            try:
                                import json as json_lib
                                images = json_lib.loads(images)
                            except:
                                images = []
                        
                        image_url = images[0] if images else "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800"
                        
                        # Parse year
                        year = car_data.get("year", 2023)
                        if isinstance(year, str):
                            try:
                                year = int(year)
                            except:
                                year = 2023
                        
                        # Parse price
                        price = car_data.get("price", 0)
                        if isinstance(price, str):
                            try:
                                price = float(price)
                            except:
                                price = 0
                        
                        # Parse mileage
                        km_age = car_data.get("km_age", 0)
                        if isinstance(km_age, str):
                            try:
                                km_age = int(km_age)
                            except:
                                km_age = 0
                        
                        # Parse engine volume
                        displacement = car_data.get("displacement", "0")
                        if isinstance(displacement, str):
                            try:
                                displacement = float(displacement) if displacement else 0
                            except:
                                displacement = 0
                        engine_volume = int(displacement * 1000) if displacement else None
                        
                        # Parse power
                        power_raw = car_data.get("power", 0)
                        if isinstance(power_raw, str):
                            try:
                                power = int(power_raw) if power_raw else 0
                            except:
                                power = 0
                        else:
                            power = power_raw or 0
                        
                        car = {
                            "id": f"che168-{item.get('inner_id', item.get('id', ''))}",
                            "inner_id": item.get("inner_id", ""),
                            "brand": car_data.get("mark", "Unknown"),
                            "brand_cn": "",
                            "model": car_data.get("model", "Unknown"),
                            "model_cn": "",
                            "year_from": year,
                            "year_to": year,
                            "price_from_cny": price,
                            "price_to_cny": price,
                            "engine_type": Che168API.map_engine_type(car_data.get("engine_type", "")),
                            "engine_volume": engine_volume,
                            "body_type": Che168API.map_body_type(car_data.get("body_type", "")),
                            "image_url": image_url,
                            "images": images,
                            "description": car_data.get("description", ""),
                            "features": [],
                            "popularity": 80,
                            "mileage": km_age if km_age else None,
                            "source": "che168",
                            "source_url": car_data.get("url", ""),
                            "fuel_type": car_data.get("engine_type", "Бензин"),
                            "transmission": car_data.get("transmission_type", ""),
                            "color": car_data.get("color", ""),
                            "address": car_data.get("address", ""),
                            "vin": car_data.get("vin", ""),
                            "power": power,
                            "drive_type": car_data.get("drive_type", ""),
                            "is_dealer": car_data.get("is_dealer", False),
                            "offer_created": car_data.get("offer_created", "")
                        }
                        cars.append(car)
                    
                    # Estimate total pages (API doesn't return total count directly)
                    next_page = meta.get("next_page")
                    has_more = next_page is not None
                    
                    result_data = {
                        "cars": cars,
                        "total": len(cars) * 100 if has_more else len(cars),  # Estimate
                        "page": page,
                        "pages": page + 10 if has_more else page,  # Estimate
                        "has_more": has_more
                    }
                    
                    set_cache(cache_key, result_data)
                    return result_data
                    
        except Exception as e:
            logger.error(f"Che168API.search_cars error: {e}")
        
        return {"cars": [], "total": 0, "page": 1, "pages": 1, "has_more": False}
    
    @staticmethod
    async def get_offer_details(inner_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific car"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{Che168API.BASE_URL}/offer",
                    params={"api_key": Che168API.API_KEY, "inner_id": inner_id}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Che168API.get_offer_details error: {e}")
        return None

# ==================== PRO-AUCTIONS PARSER ====================

class ProAuctionsParser:
    """Parser for demo.pro-auctions.ru/china-used/ catalog"""
    
    BASE_URL = "https://demo.pro-auctions.ru/china-used/"
    
    @staticmethod
    def parse_price_rub(text: str) -> Optional[int]:
        """Extract price in RUB from string like '1 513 051 ₽'"""
        if not text:
            return None
        # Remove all non-digits except decimal points
        cleaned = re.sub(r'[^\d]', '', text.strip())
        try:
            return int(cleaned) if cleaned else None
        except ValueError:
            return None
    
    @staticmethod
    def parse_mileage(text: str) -> Optional[int]:
        """Extract mileage from string like '2 600 км'"""
        if not text:
            return None
        match = re.search(r'([\d\s]+)\s*км', text)
        if match:
            cleaned = re.sub(r'\s', '', match.group(1))
            try:
                return int(cleaned)
            except ValueError:
                return None
        return None
    
    @staticmethod
    def parse_year_month(text: str) -> tuple:
        """Extract year and month from string like '1 / 2025 г' or '6 / 2024 г'"""
        if not text:
            return None, None
        match = re.search(r'(\d+)\s*/\s*(\d{4})', text)
        if match:
            return int(match.group(2)), int(match.group(1))
        return None, None
    
    @staticmethod
    def parse_engine_volume(text: str) -> Optional[int]:
        """Extract engine volume from string like '1499 см³'"""
        if not text:
            return None
        match = re.search(r'(\d+)\s*см', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
    
    @staticmethod
    def determine_engine_type(fuel_text: str) -> str:
        """Determine engine type from fuel text"""
        if not fuel_text:
            return "ice"
        fuel_lower = fuel_text.lower()
        if 'электр' in fuel_lower or 'electric' in fuel_lower:
            return "electric"
        elif 'гибрид' in fuel_lower or 'hybrid' in fuel_lower or 'phev' in fuel_lower:
            return "hybrid"
        return "ice"
    
    @staticmethod
    def determine_body_type(body_text: str) -> str:
        """Determine body type from text"""
        if not body_text:
            return "sedan"
        body_lower = body_text.lower()
        if 'кроссовер' in body_lower or 'suv' in body_lower:
            return "suv"
        elif 'хэтчбек' in body_lower or 'хетчбек' in body_lower:
            return "hatchback"
        elif 'минивэн' in body_lower or 'mpv' in body_lower:
            return "mpv"
        elif 'универсал' in body_lower or 'wagon' in body_lower:
            return "wagon"
        elif 'пикап' in body_lower or 'pickup' in body_lower:
            return "pickup"
        return "sedan"
    
    @classmethod
    async def fetch_page(cls, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                }
                response = await client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return None
    
    @classmethod
    async def get_brands(cls) -> List[Dict]:
        """Get list of all brands from main catalog page"""
        cache_key = "pro_auctions_brands"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        html = await cls.fetch_page(cls.BASE_URL)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        brands = []
        
        # Find brand links - they can be relative (href="aito/") or absolute
        brand_links = soup.select('.brands_models__link, .car-brands__link')
        seen_brands = set()
        
        for link in brand_links:
            href = link.get('href', '')
            
            # Skip empty or non-relevant links
            if not href or href == '#' or 'javascript:' in href:
                continue
            
            # Handle relative URLs (like "aito/") and absolute URLs
            # Extract brand slug from URL
            brand_slug = href.rstrip('/').split('/')[-1]
            
            # Skip if looks like a model URL (contains parent brand slug)
            # Brand URLs: aito/, geely/, etc. Model URLs: geely/emgrand/, etc.
            parts = href.rstrip('/').split('/')
            if len(parts) > 2:  # This is a model URL, skip it
                continue
            
            if brand_slug and brand_slug not in seen_brands:
                spans = link.find_all('span')
                
                # Try different methods to extract name and count
                if spans and len(spans) >= 2:
                    # Format: <span>Brand</span><span>1 234</span>
                    brand_name = spans[0].get_text(strip=True)
                    count_text = spans[1].get_text(strip=True)
                elif spans and len(spans) == 1:
                    # Only one span - just brand name
                    brand_name = spans[0].get_text(strip=True)
                    count_text = "0"
                else:
                    # No spans - text is directly in link
                    full_text = link.get_text(strip=True)
                    brand_name = full_text
                    count_text = "0"
                
                # Extract count - handle "1 234" format with spaces
                count = 0
                if count_text:
                    # Remove all non-digit characters and convert
                    digits = re.sub(r'[^\d]', '', count_text)
                    if digits:
                        try:
                            count = int(digits)
                        except ValueError:
                            count = 0
                
                if brand_name and not brand_name.startswith('...') and not brand_name.startswith('Показать'):
                    seen_brands.add(brand_slug)
                    # Build full URL for the brand
                    full_url = f"{cls.BASE_URL}{brand_slug}/"
                    brands.append({
                        "name": brand_name,
                        "slug": brand_slug,
                        "count": count,
                        "url": full_url
                    })
        
        # Sort by count descending
        brands.sort(key=lambda x: x["count"], reverse=True)
        set_cache(cache_key, brands)
        return brands
    
    @classmethod
    async def get_models(cls, brand_slug: str) -> List[Dict]:
        """Get list of all models for a specific brand from the brand page"""
        cache_key = f"pro_auctions_models_{brand_slug}"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        url = f"{cls.BASE_URL}{brand_slug}/"
        html = await cls.fetch_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        models = []
        seen_models = set()
        
        # Find model links in the brands_models_list section
        model_links = soup.select('.brands_models__link')
        
        for link in model_links:
            href = link.get('href', '')
            if not href or href == '#':
                continue
            
            # Extract model slug from URL (e.g., "binrui/" -> "binrui")
            model_slug = href.rstrip('/').split('/')[-1]
            
            if model_slug and model_slug not in seen_models:
                spans = link.find_all('span')
                
                if spans and len(spans) >= 2:
                    model_name = spans[0].get_text(strip=True)
                    count_text = spans[1].get_text(strip=True)
                elif spans and len(spans) == 1:
                    model_name = spans[0].get_text(strip=True)
                    count_text = "0"
                else:
                    model_name = link.get_text(strip=True)
                    count_text = "0"
                
                # Extract count
                count = 0
                if count_text:
                    digits = re.sub(r'[^\d]', '', count_text)
                    if digits:
                        try:
                            count = int(digits)
                        except ValueError:
                            count = 0
                
                if model_name and model_name not in ['Показать все', '...']:
                    seen_models.add(model_slug)
                    models.append({
                        "name": model_name,
                        "slug": model_slug,
                        "count": count
                    })
        
        # Sort by count descending
        models.sort(key=lambda x: x["count"], reverse=True)
        set_cache(cache_key, models)
        return models
    
    @classmethod
    async def search_cars(cls, brand: str = None, model: str = None, page: int = 1, limit: int = 20) -> Dict:
        """Search cars from catalog with optional brand and model filter"""
        cache_key = f"pro_auctions_cars_{brand or 'all'}_{model or 'all'}_{page}_{limit}"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        # Build URL - can include brand and model
        if brand and model:
            url = f"{cls.BASE_URL}{brand}/{model}/"
        elif brand:
            url = f"{cls.BASE_URL}{brand}/"
        else:
            url = cls.BASE_URL
        
        html = await cls.fetch_page(url)
        if not html:
            return {"cars": [], "total": 0, "pages": 1}
        
        soup = BeautifulSoup(html, 'lxml')
        cars = []
        
        # Find car cards
        car_cards = soup.select('.card-row')
        
        for card in car_cards:
            try:
                car_data = cls._parse_car_card(card)
                if car_data:
                    cars.append(car_data)
            except Exception as e:
                logger.error(f"Error parsing car card: {e}")
                continue
        
        # Get total count
        total_text = soup.select_one('.catalog__qnt span')
        total = int(re.sub(r'\D', '', total_text.get_text())) if total_text else len(cars)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_cars = cars[start:end]
        
        pages = max(1, (total + limit - 1) // limit)
        
        result = {
            "cars": paginated_cars,
            "total": total,
            "pages": pages,
            "page": page
        }
        
        set_cache(cache_key, result)
        return result
    
    @classmethod
    def _parse_car_card(cls, card) -> Optional[Dict]:
        """Parse single car card HTML element"""
        # Get car name and URL
        name_link = card.select_one('.card-row__name')
        if not name_link:
            return None
        
        car_name = name_link.get_text(strip=True)
        car_url = name_link.get('href', '')
        
        # Extract brand and model from name (e.g., "Geely Emgrand")
        name_parts = car_name.split(' ', 1)
        brand = name_parts[0] if name_parts else ""
        model = name_parts[1] if len(name_parts) > 1 else car_name
        
        # Get car ID from URL
        car_id = car_url.rstrip('/').split('/')[-1] if car_url else str(uuid.uuid4())
        
        # Get image from meta itemprop="image" - most reliable
        image_url = None
        images = []
        
        # First try meta tag with itemprop="image"
        meta_image = card.select_one('meta[itemprop="image"]')
        if meta_image:
            content = meta_image.get('content', '')
            if content and 'pa-server.ru' in content:
                image_url = content
                images.append(content)
        
        # Also try to extract images from JSON in comments
        card_html = str(card)
        import json as json_module
        json_match = re.search(r'"images":\[([^\]]+)\]', card_html)
        if json_match:
            try:
                # Parse the images array
                images_str = '[' + json_match.group(1) + ']'
                # Clean escaped URLs
                images_str = images_str.replace('\\/', '/')
                parsed_images = json_module.loads(images_str)
                for img in parsed_images[:5]:  # Limit to 5 images
                    if img not in images:
                        images.append(img)
                if not image_url and parsed_images:
                    image_url = parsed_images[0]
            except:
                pass
        
        # Fallback to default image if nothing found
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800"
        
        # Get price in CNY from data-calc attribute
        price_cny = 0
        year = None
        month = None
        engine_volume = None
        fuel_type = "Бензин"
        engine_type = "ice"
        
        price_toggle = card.select_one('.js-price-popup, [data-calc]')
        if price_toggle:
            data_calc = price_toggle.get('data-calc', '')
            # Parse data-calc: "price=52000&year=2022&month=12&v=1499&m=b..."
            params = dict(param.split('=') for param in data_calc.split('&') if '=' in param)
            
            if 'price' in params:
                try:
                    price_cny = int(params['price'])
                except ValueError:
                    price_cny = 0
            
            if 'year' in params:
                try:
                    year = int(params['year'])
                except ValueError:
                    pass
            
            if 'month' in params:
                try:
                    month = int(params['month'])
                except ValueError:
                    pass
            
            if 'v' in params:
                try:
                    engine_volume = int(params['v'])
                except ValueError:
                    pass
            
            # Determine engine type from m parameter (b=benzin, d=diesel, e=electric, h=hybrid)
            m_param = params.get('m', 'b').lower()
            
            # Check for electric power first - this is more reliable
            power_electro = params.get('powerElectro', '0')
            power_dvs = params.get('powerDVS', '0')
            
            # Convert to float for comparison
            try:
                electro_val = float(power_electro) if power_electro else 0
                dvs_val = float(power_dvs) if power_dvs else 0
            except ValueError:
                electro_val = 0
                dvs_val = 0
            
            if electro_val > 0 and dvs_val > 0:
                engine_type = "hybrid"
                fuel_type = "Гибрид"
            elif electro_val > 0 and dvs_val == 0:
                engine_type = "electric"
                fuel_type = "Электро"
            elif m_param == 'e':
                engine_type = "electric"
                fuel_type = "Электро"
            elif m_param == 'h':
                engine_type = "hybrid"
                fuel_type = "Гибрид"
            elif m_param == 'd':
                engine_type = "ice"
                fuel_type = "Дизель"
            else:
                engine_type = "ice"
                fuel_type = "Бензин"
        
        # Fallback: Get age info (mileage and year) from visible text if not from data-calc
        mileage = None
        age_div = card.select_one('.card-row__age')
        
        if age_div:
            spans = age_div.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)
                if 'км' in text:
                    mileage = cls.parse_mileage(text)
                elif '/' in text and 'г' in text and not year:
                    year, month = cls.parse_year_month(text)
        
        # Get body type from info columns
        body_type = "sedan"
        source_url = ""
        info_cols = card.select('.card-row__col')
        
        for col in info_cols:
            text = col.get_text(strip=True)
            if any(bt in text for bt in ['Седан', 'Кроссовер', 'Хэтчбек', 'Минивэн', 'Универсал', 'Пикап', 'SUV']):
                body_type = cls.determine_body_type(text)
            elif 'dongchedi' in text.lower() or 'che168' in text.lower():
                ext_link = col.select_one('a')
                if ext_link:
                    source_url = ext_link.get('href', '')
        
        return {
            "id": car_id,
            "brand": brand,
            "brand_cn": "",
            "model": model,
            "model_cn": "",
            "year_from": year or 2023,
            "year_to": year,
            "price_from_cny": price_cny,
            "price_to_cny": price_cny,
            "engine_type": engine_type,
            "engine_volume": engine_volume,
            "body_type": body_type,
            "mileage": mileage,
            "image_url": image_url,
            "images": images,
            "description": f"{car_name} - {year or 2023} г., пробег {mileage or 0} км",
            "features": [],
            "source": "pro-auctions",
            "source_url": source_url,
            "popularity": 50,
            "fuel_type": fuel_type
        }

# ==================== AUTH HELPERS ====================

def create_token(user_id: str, email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"sub": user_id, "email": email, "exp": expiration}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

# ==================== AUTH ENDPOINTS ====================

# Admin email - automatically gets admin role
ADMIN_EMAILS = ["votin@tut.by", "admin@carbridge.by"]

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine role - admin emails get admin role automatically
    role = "admin" if user.email in ADMIN_EMAILS else "user"
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "user_type": user.user_type,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user.email)
    user_response = UserResponse(
        id=user_id, email=user.email, name=user.name,
        phone=user.phone, user_type=user.user_type, role=role, created_at=user_doc["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
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

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"], name=current_user["name"],
        phone=current_user.get("phone"), user_type=current_user["user_type"],
        role=current_user.get("role", "user"), created_at=current_user["created_at"]
    )

# ==================== ROLE MANAGEMENT ENDPOINTS ====================

def require_role(allowed_roles: list):
    """Dependency to check if user has required role"""
    async def check_role(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(require_role(["admin"]))):
    """Get all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(500)
    return users

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, current_user: dict = Depends(require_role(["admin"]))):
    """Update user role (admin only)"""
    new_role = role_data.get("role")
    if new_role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ROLES}")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": new_role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {new_role}"}

class BalanceUpdate(BaseModel):
    amount: float
    reason: Optional[str] = None

@api_router.post("/admin/users/{user_id}/balance")
async def update_user_balance(user_id: str, data: BalanceUpdate, current_user: dict = Depends(require_role(["admin"]))):
    """Add or subtract balance from user account (admin only)"""
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Get current account or create
    account = await db.accounts.find_one({"user_id": user_id})
    current_balance = account.get("balance", 0.0) if account else 0.0
    
    new_balance = current_balance + data.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Баланс не может быть отрицательным")
    
    # Update or create account
    await db.accounts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "balance": new_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$setOnInsert": {
                "is_verified": False,
                "contract_signed": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Record transaction
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "admin_adjustment",
        "amount": data.amount,
        "reason": data.reason or "Корректировка администратором",
        "admin_id": current_user["id"],
        "admin_email": current_user["email"],
        "balance_before": current_balance,
        "balance_after": new_balance,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.balance_transactions.insert_one(transaction_doc)
    
    return {
        "message": f"Баланс {'начислен' if data.amount > 0 else 'списан'}",
        "amount": data.amount,
        "new_balance": new_balance,
        "user_email": user.get("email")
    }

@api_router.get("/admin/users/{user_id}/account")
async def get_user_account_admin(user_id: str, current_user: dict = Depends(require_role(["admin"]))):
    """Get user account details (admin only)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    account = await db.accounts.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get recent transactions
    transactions = await db.balance_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "user": user,
        "account": account or {"balance": 0.0, "is_verified": False, "contract_signed": False},
        "transactions": transactions
    }

# ==================== MODERATOR USER MANAGEMENT ENDPOINTS ====================

# Deal stages that require moderator approval
DEAL_STAGES = ["verification", "contract", "inspection", "payment", "export", "logistics", "delivery"]

@api_router.get("/moderator/users/{user_id}/full-profile")
async def get_user_full_profile(user_id: str, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get complete user profile with all data for moderator review"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    account = await db.accounts.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get user's cars in garage
    cars = await db.garage.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get user's tenders
    tenders = await db.tenders.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get user's documents
    documents = await db.documents.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get user's deals
    deals = await db.deals.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get affiliate status if exists
    affiliate = await db.affiliates.find_one({"user_id": user_id}, {"_id": 0})
    
    return {
        "user": user,
        "account": account or {
            "balance": 0.0, 
            "is_verified": False, 
            "contract_signed": False,
            "verification_status": "pending"
        },
        "cars": cars,
        "tenders": tenders,
        "documents": documents,
        "deals": deals,
        "affiliate": affiliate
    }

@api_router.post("/moderator/users/{user_id}/verify")
async def verify_user(user_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Verify or reject user verification"""
    action = data.get("action")  # "approve" or "reject"
    reason = data.get("reason", "")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    is_verified = action == "approve"
    verification_status = "approved" if is_verified else "rejected"
    
    await db.accounts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "is_verified": is_verified,
                "verification_status": verification_status,
                "verification_date": datetime.now(timezone.utc).isoformat(),
                "verified_by": current_user["id"],
                "verified_by_name": current_user.get("name", ""),
                "verification_reason": reason
            },
            "$setOnInsert": {
                "balance": 0.0,
                "contract_signed": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Log moderation action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user_verification",
        "target_type": "user",
        "target_id": user_id,
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": verification_status,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Пользователь {'верифицирован' if is_verified else 'отклонён'}",
        "is_verified": is_verified,
        "verification_status": verification_status
    }

@api_router.post("/moderator/users/{user_id}/sign-contract")
async def sign_user_contract(user_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Approve or sign user contract"""
    action = data.get("action")  # "approve" or "reject"
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    contract_signed = action == "approve"
    
    await db.accounts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "contract_signed": contract_signed,
                "contract_status": "signed" if contract_signed else "rejected",
                "contract_date": datetime.now(timezone.utc).isoformat(),
                "contract_approved_by": current_user["id"]
            }
        },
        upsert=True
    )
    
    return {
        "message": f"Договор {'подписан' if contract_signed else 'отклонён'}",
        "contract_signed": contract_signed
    }

@api_router.post("/moderator/documents/{doc_id}/verify")
async def verify_document(doc_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Verify a user document"""
    action = data.get("action")  # "approve" or "reject"
    comment = data.get("comment", "")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    is_verified = action == "approve"
    
    await db.documents.update_one(
        {"id": doc_id},
        {
            "$set": {
                "is_verified": is_verified,
                "verification_status": "approved" if is_verified else "rejected",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": current_user["id"],
                "verified_by_name": current_user.get("name", ""),
                "verification_comment": comment
            }
        }
    )
    
    # Log moderation action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "document_verification",
        "target_type": "document",
        "target_id": doc_id,
        "user_id": doc.get("user_id"),
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": "approved" if is_verified else "rejected",
        "comment": comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Документ {'проверен' if is_verified else 'отклонён'}",
        "is_verified": is_verified
    }

@api_router.post("/moderator/deals/{deal_id}/approve-stage")
async def approve_deal_stage(deal_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Approve current deal stage and allow progression to next stage"""
    action = data.get("action")  # "approve" or "reject"
    comment = data.get("comment", "")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    current_stage = deal.get("current_stage", "verification")
    is_approved = action == "approve"
    
    # Update stage approval
    stage_approvals = deal.get("stage_approvals", {})
    stage_approvals[current_stage] = {
        "approved": is_approved,
        "approved_by": current_user["id"],
        "approved_by_name": current_user.get("name", ""),
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "comment": comment
    }
    
    update_data = {
        "stage_approvals": stage_approvals,
        f"stages.{current_stage}.moderator_approved": is_approved,
        f"stages.{current_stage}.approval_date": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # If approved, move to next stage
    next_stage = None
    if is_approved:
        current_idx = DEAL_STAGES.index(current_stage) if current_stage in DEAL_STAGES else 0
        if current_idx < len(DEAL_STAGES) - 1:
            next_stage = DEAL_STAGES[current_idx + 1]
            update_data["current_stage"] = next_stage
            update_data["can_proceed"] = True
        else:
            # Final stage
            update_data["status"] = "completed"
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update_data["can_proceed"] = False
        update_data["rejection_reason"] = comment
    
    await db.deals.update_one({"id": deal_id}, {"$set": update_data})
    
    # Log moderation action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "deal_stage_approval",
        "target_type": "deal",
        "target_id": deal_id,
        "stage": current_stage,
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": "approved" if is_approved else "rejected",
        "comment": comment,
        "next_stage": next_stage,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Этап '{current_stage}' {'одобрен' if is_approved else 'отклонён'}",
        "current_stage": current_stage,
        "next_stage": next_stage if is_approved else None,
        "can_proceed": is_approved
    }

@api_router.get("/moderator/deals/{deal_id}")
async def get_deal_details(deal_id: str, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get detailed deal information for moderator"""
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Get related user
    user = await db.users.find_one({"id": deal.get("user_id")}, {"_id": 0, "password_hash": 0})
    
    # Get related car
    car = await db.garage.find_one({"id": deal.get("car_id")}, {"_id": 0})
    
    # Get related documents
    documents = await db.documents.find(
        {"deal_id": deal_id},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "deal": deal,
        "user": user,
        "car": car,
        "documents": documents,
        "stages": DEAL_STAGES
    }

@api_router.post("/deals/create")
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
            "calculated_price_usd": car.get("calculated_price_usd")
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

@api_router.get("/deals")
async def get_user_deals(current_user: dict = Depends(get_current_user)):
    """Get all deals for current user"""
    deals = await db.deals.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return deals

@api_router.get("/deals/{deal_id}")
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

DEAL_ADD_FEE = 300  # $300 to add car to deal (free if from tender)
CONSULTANT_FEE = 200  # $200 for consultant help

@api_router.post("/deals/add-car")
async def add_car_to_deal(data: dict, current_user: dict = Depends(get_current_user)):
    """Add car to deal from garage (charges $300) or from tender (free)"""
    car_id = data.get("car_id")
    from_tender = data.get("from_tender", False)
    tender_offer_id = data.get("tender_offer_id")
    
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
    
    # Get car info
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    # Create deal
    deal_id = str(uuid.uuid4())
    
    deal_doc = {
        "id": deal_id,
        "user_id": current_user["id"],
        "car_id": car_id,
        "tender_offer_id": tender_offer_id,
        "from_tender": from_tender,
        "car_info": {
            "brand": car.get("brand"),
            "model": car.get("model"),
            "year": car.get("year"),
            "price_cny": car.get("price_cny"),
            "price_usd": car.get("calculated_price_usd") or car.get("price_usd"),
            "image_url": car.get("image_url")
        },
        "status": "active",
        "current_stage": "leasing",
        "stages": {
            "leasing": {"status": "pending", "completed": False, "skipped": False},
            "inspection": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "price": None},
            "export": {"status": "pending", "completed": False, "contractor_id": None, "price": None},
            "logistics_china": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "price": None},
            "insurance": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "price": None},
            "delivery_rb": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "price": None},
            "customs": {"status": "pending", "completed": False, "skipped": False, "contractor_id": None, "price": None},
            "completion": {"status": "pending", "completed": False}
        },
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

@api_router.post("/deals/{deal_id}/select-contractor")
async def select_contractor_for_stage(deal_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Select contractor for a deal stage"""
    stage = data.get("stage")  # inspection, export, logistics
    contractor_id = data.get("contractor_id")
    price = data.get("price", 0)
    
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Allowed stages for contractor selection
    allowed_stages = ["inspection", "export", "logistics_china", "insurance", "delivery_rb", "customs"]
    if stage not in allowed_stages:
        raise HTTPException(status_code=400, detail="Неверный этап")
    
    # Update deal with contractor selection
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                f"stages.{stage}.contractor_id": contractor_id,
                f"stages.{stage}.price": price,
                f"stages.{stage}.status": "contractor_selected",
                f"contractors.{stage}": contractor_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": f"Подрядчик выбран для этапа {stage}"}

@api_router.post("/deals/{deal_id}/pay-stage")
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
    
    return {"message": "Оплата прошла успешно", "new_balance": balance - amount}

@api_router.post("/deals/{deal_id}/skip-leasing")
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

@api_router.post("/deals/{deal_id}/request-leasing")
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

@api_router.post("/deals/{deal_id}/complete-stage")
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

# ==================== NEW DEAL STAGES ENDPOINTS ====================

# Platform commission constants
PLATFORM_COMMISSION = 0.03  # 3%
PLATFORM_PAYMENT_FEE = 0.01  # +1% if paid through platform

# New stages list
NEW_DEAL_STAGES = [
    "leasing", "inspection", "export", "logistics_china", 
    "insurance", "delivery_rb", "customs", "completion"
]

@api_router.post("/deals/{deal_id}/skip-stage")
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

@api_router.post("/deals/{deal_id}/leasing-request")
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

@api_router.post("/deals/{deal_id}/pay-invoice")
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

@api_router.post("/deals/{deal_id}/complete")
async def complete_deal(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Complete the deal"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if export stage is completed (minimum requirement)
    export_stage = deal.get("stages", {}).get("export", {})
    if not export_stage.get("completed") and not export_stage.get("paid"):
        raise HTTPException(status_code=400, detail="Для завершения сделки необходимо завершить этап 'Экспорт'")
    
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {
                "status": "completed",
                "stages.completion.completed": True,
                "current_stage": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update car status
    await db.garage.update_one(
        {"id": deal.get("car_id")},
        {"$set": {"status": "delivered"}}
    )
    
    return {"message": "Сделка успешно завершена!"}

# ==================== END NEW DEAL STAGES ENDPOINTS ====================

@api_router.post("/consultant/request")
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

@api_router.get("/account/summary")
async def get_account_summary(current_user: dict = Depends(get_current_user)):
    """Get account summary for dashboard"""
    account = await db.accounts.find_one({"user_id": current_user["id"]}, {"_id": 0})
    verification = await db.verifications.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    # Get active deal
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

@api_router.get("/moderator/pending-approvals")
async def get_pending_approvals(current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get all items pending moderator approval"""
    # Users pending verification
    pending_users = await db.accounts.find(
        {"verification_status": {"$in": [None, "pending"]}},
        {"_id": 0}
    ).to_list(100)
    
    # Get user info for pending accounts
    pending_user_ids = [u.get("user_id") for u in pending_users if u.get("user_id")]
    users_info = {}
    if pending_user_ids:
        users = await db.users.find(
            {"id": {"$in": pending_user_ids}},
            {"_id": 0, "password_hash": 0}
        ).to_list(100)
        users_info = {u["id"]: u for u in users}
    
    # Documents pending verification
    pending_documents = await db.documents.find(
        {"is_verified": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    
    # Deals pending stage approval
    pending_deals = await db.deals.find(
        {"can_proceed": False, "status": "active"},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "pending_users": [
            {**u, "user_info": users_info.get(u.get("user_id"), {})}
            for u in pending_users
        ],
        "pending_documents": pending_documents,
        "pending_deals": pending_deals
    }

# ==================== MODERATOR VERIFICATION DOCUMENTS ====================

@api_router.get("/moderator/verifications")
async def get_all_verifications(current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get all client verifications for review"""
    verifications = await db.verifications.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    # Get user info for each verification
    user_ids = [v.get("user_id") for v in verifications if v.get("user_id")]
    users_info = {}
    if user_ids:
        users = await db.users.find(
            {"id": {"$in": user_ids}},
            {"_id": 0, "password_hash": 0}
        ).to_list(200)
        users_info = {u["id"]: u for u in users}
    
    # Enrich verifications with user info
    result = []
    for v in verifications:
        user_info = users_info.get(v.get("user_id"), {})
        v["user_name"] = user_info.get("name", v.get("full_name", ""))
        v["user_email"] = user_info.get("email", v.get("email", ""))
        result.append(v)
    
    return result

@api_router.get("/moderator/verifications/pending")
async def get_pending_verifications(current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get verifications pending review"""
    verifications = await db.verifications.find(
        {"status": {"$in": ["pending", "documents_uploaded", "under_review"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get user info
    user_ids = [v.get("user_id") for v in verifications if v.get("user_id")]
    users_info = {}
    if user_ids:
        users = await db.users.find(
            {"id": {"$in": user_ids}},
            {"_id": 0, "password_hash": 0}
        ).to_list(100)
        users_info = {u["id"]: u for u in users}
    
    result = []
    for v in verifications:
        user_info = users_info.get(v.get("user_id"), {})
        v["user_name"] = user_info.get("name", v.get("full_name", ""))
        v["user_email"] = user_info.get("email", v.get("email", ""))
        result.append(v)
    
    return result

@api_router.get("/moderator/verifications/{verification_id}")
async def get_verification_details(verification_id: str, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get detailed verification info including documents"""
    verification = await db.verifications.find_one(
        {"id": verification_id},
        {"_id": 0}
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    # Get user info
    user = await db.users.find_one(
        {"id": verification.get("user_id")},
        {"_id": 0, "password_hash": 0}
    )
    
    verification["user"] = user
    return verification

@api_router.post("/moderator/verifications/{verification_id}/review")
async def review_verification(verification_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Approve or reject client verification"""
    action = data.get("action")  # "approve" or "reject"
    comment = data.get("comment", "")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    verification = await db.verifications.find_one({"id": verification_id})
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    is_approved = action == "approve"
    new_status = "approved" if is_approved else "rejected"
    
    await db.verifications.update_one(
        {"id": verification_id},
        {
            "$set": {
                "status": new_status,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "reviewed_by": current_user["id"],
                "reviewed_by_name": current_user.get("name", ""),
                "review_comment": comment,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update user account verification status
    await db.accounts.update_one(
        {"user_id": verification.get("user_id")},
        {
            "$set": {
                "is_verified": is_approved,
                "verification_status": new_status,
                "verification_date": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Log action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "client_verification_review",
        "target_type": "verification",
        "target_id": verification_id,
        "user_id": verification.get("user_id"),
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": new_status,
        "comment": comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Верификация {'подтверждена' if is_approved else 'отклонена'}",
        "status": new_status
    }

@api_router.post("/moderator/verifications/{verification_id}/documents/{doc_id}/verify")
async def verify_client_document(verification_id: str, doc_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Verify a specific document within client verification"""
    action = data.get("action")  # "approve" or "reject"
    comment = data.get("comment", "")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    verification = await db.verifications.find_one({"id": verification_id})
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    # Find document in verification
    documents = verification.get("documents", [])
    doc_found = False
    
    for doc in documents:
        if doc.get("id") == doc_id:
            doc["verified"] = action == "approve"
            doc["verification_status"] = "approved" if action == "approve" else "rejected"
            doc["verified_at"] = datetime.now(timezone.utc).isoformat()
            doc["verified_by"] = current_user["id"]
            doc["verification_comment"] = comment
            doc_found = True
            break
    
    if not doc_found:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    # Update verification with modified documents
    await db.verifications.update_one(
        {"id": verification_id},
        {
            "$set": {
                "documents": documents,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Log action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "document_verification",
        "target_type": "verification_document",
        "target_id": doc_id,
        "verification_id": verification_id,
        "user_id": verification.get("user_id"),
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": "approved" if action == "approve" else "rejected",
        "comment": comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Документ {'подтверждён' if action == 'approve' else 'отклонён'}",
        "verified": action == "approve"
    }

@api_router.get("/user/role")
async def get_user_role(current_user: dict = Depends(get_current_user)):
    """Get current user's role"""
    return {"role": current_user.get("role", "user")}

# ==================== USER ACCOUNT ENDPOINT ====================

@api_router.get("/user/account")
async def get_user_account(current_user: dict = Depends(get_current_user)):
    """Get user account details including balance, verification status, and contract status"""
    # Try to get account from database, create if not exists
    account = await db.accounts.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    if not account:
        # Create default account
        account = {
            "user_id": current_user["id"],
            "balance": 0.0,
            "is_verified": False,
            "contract_signed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.accounts.insert_one(account)
        # Remove _id before returning
        account.pop("_id", None)
    
    return {
        "balance": account.get("balance", 0.0),
        "is_verified": account.get("is_verified", False),
        "contract_signed": account.get("contract_signed", False)
    }

@api_router.post("/user/account/deposit")
async def deposit_to_account(amount: float, current_user: dict = Depends(get_current_user)):
    """Deposit funds to user account"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    result = await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": amount}},
        upsert=True
    )
    
    return {"message": f"Successfully deposited ${amount}", "new_balance": amount}

# ==================== AFFILIATE PROGRAM ENDPOINTS ====================

COMMISSION_RATE = 0.03  # 3% platform commission
AFFILIATE_SHARE = 0.20  # 20% of commission goes to affiliate
PARTNER_THRESHOLD = 3   # 3 completed deals to become partner

def generate_referral_code(user_id: str) -> str:
    """Generate unique referral code from user id"""
    import hashlib
    hash_obj = hashlib.md5(user_id.encode())
    return f"CB{hash_obj.hexdigest()[:8].upper()}"

@api_router.post("/affiliate/register", response_model=AffiliateResponse)
async def register_as_affiliate(data: AffiliateRegister, current_user: dict = Depends(get_current_user)):
    """Register user in affiliate program"""
    # Check if already registered
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
    
    # Generate referral link
    affiliate_doc["referral_link"] = f"https://carbridge.by/?ref={referral_code}"
    
    return AffiliateResponse(**affiliate_doc)

@api_router.get("/affiliate/status", response_model=AffiliateResponse)
async def get_affiliate_status(current_user: dict = Depends(get_current_user)):
    """Get current user's affiliate status"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    affiliate["referral_link"] = f"https://carbridge.by/?ref={affiliate['referral_code']}"
    return AffiliateResponse(**affiliate)

@api_router.get("/affiliate/referrals")
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

@api_router.get("/affiliate/transactions")
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

@api_router.post("/affiliate/withdraw")
async def withdraw_affiliate_earnings(request: WithdrawRequest, current_user: dict = Depends(get_current_user)):
    """Withdraw affiliate earnings"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть положительной")
    
    if request.amount > affiliate.get("available_balance", 0):
        raise HTTPException(status_code=400, detail="Недостаточно средств для вывода")
    
    # Create withdrawal request
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
    
    # If transferring to platform balance, do it immediately
    if request.method == "platform_balance":
        await db.accounts.update_one(
            {"user_id": current_user["id"]},
            {"$inc": {"balance": request.amount}},
            upsert=True
        )
        withdrawal_doc["status"] = "completed"
        withdrawal_doc["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.affiliate_withdrawals.insert_one(withdrawal_doc)
    
    # Update affiliate balance
    await db.affiliates.update_one(
        {"user_id": current_user["id"]},
        {
            "$inc": {
                "available_balance": -request.amount,
                "withdrawn_earnings": request.amount
            }
        }
    )
    
    # Record transaction
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

@api_router.post("/affiliate/register-referral")
async def register_referral(referral_code: str, current_user: dict = Depends(get_current_user)):
    """Register a user as referral (called when user signs up with referral code)"""
    # Find affiliate by referral code
    affiliate = await db.affiliates.find_one({"referral_code": referral_code})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Неверный реферальный код")
    
    # Can't refer yourself
    if affiliate["user_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Нельзя использовать собственный реферальный код")
    
    # Check if already a referral
    existing = await db.referrals.find_one({"referral_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже зарегистрированы как реферал")
    
    # Create referral record
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
    
    # Update affiliate stats
    await db.affiliates.update_one(
        {"user_id": affiliate["user_id"]},
        {"$inc": {"total_referrals": 1, "active_referrals": 1}}
    )
    
    # Update user to mark as referral
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"referred_by": affiliate["user_id"], "referral_code_used": referral_code}}
    )
    
    return {"message": "Реферальный код применён", "affiliate_name": affiliate.get("user_name", "")}

@api_router.post("/affiliate/record-commission")
async def record_affiliate_commission(
    referral_user_id: str,
    deal_amount: float,
    deal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Record commission for affiliate when referral completes a deal (internal use)"""
    # This would be called internally when a deal is completed
    # Check if user is a referral
    referral = await db.referrals.find_one({"referral_id": referral_user_id})
    if not referral:
        return {"message": "User is not a referral"}
    
    affiliate_id = referral["affiliate_id"]
    
    # Calculate commission (20% of 3% platform commission)
    platform_commission = deal_amount * COMMISSION_RATE
    affiliate_commission = platform_commission * AFFILIATE_SHARE
    
    # Update referral stats
    await db.referrals.update_one(
        {"referral_id": referral_user_id},
        {
            "$inc": {
                "completed_deals": 1,
                "total_commission": affiliate_commission
            }
        }
    )
    
    # Update affiliate stats
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
            {"$set": {"is_partner": True, "partner_since": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Record transaction
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

@api_router.get("/affiliate/check/{referral_code}")
async def check_referral_code(referral_code: str):
    """Check if referral code is valid (public endpoint)"""
    affiliate = await db.affiliates.find_one({"referral_code": referral_code}, {"_id": 0, "user_name": 1, "is_partner": 1})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")
    
    return {
        "valid": True,
        "partner_name": affiliate.get("user_name", "Партнёр CarBridge"),
        "is_verified_partner": affiliate.get("is_partner", False)
    }

# ==================== GARAGE ENDPOINTS ====================

@api_router.post("/garage", response_model=CarResponse)
async def add_car_to_garage(car: CarCreate, current_user: dict = Depends(get_current_user)):
    car_id = str(uuid.uuid4())
    car_doc = {
        "id": car_id,
        "user_id": current_user["id"],
        **car.model_dump(),
        "status": "saved",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.garage.insert_one(car_doc)
    return CarResponse(**car_doc)

@api_router.get("/garage", response_model=List[CarResponse])
async def get_garage(current_user: dict = Depends(get_current_user)):
    cars = await db.garage.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return [CarResponse(**car) for car in cars]

@api_router.get("/garage/{car_id}", response_model=CarResponse)
async def get_car(car_id: str, current_user: dict = Depends(get_current_user)):
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]}, {"_id": 0})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarResponse(**car)

@api_router.delete("/garage/{car_id}")
async def delete_car(car_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.garage.delete_one({"id": car_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted"}

class CarUpdate(BaseModel):
    year: Optional[int] = None
    mileage: Optional[int] = None
    price_cny: Optional[float] = None
    engine_type: Optional[Literal["ice", "hybrid", "electric"]] = None
    engine_volume: Optional[int] = None
    notes: Optional[str] = None

@api_router.put("/garage/{car_id}", response_model=CarResponse)
async def update_car(car_id: str, car_update: CarUpdate, current_user: dict = Depends(get_current_user)):
    """Update car details in garage"""
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    update_data = {}
    if car_update.year is not None:
        update_data["year"] = car_update.year
    if car_update.mileage is not None:
        update_data["mileage"] = car_update.mileage
    if car_update.price_cny is not None:
        update_data["price_cny"] = car_update.price_cny
        # Recalculate Belarus price if price changed
        try:
            current_year = datetime.now().year
            car_age = current_year - (car_update.year or car.get("year", current_year))
            age_category = "under3" if car_age < 3 else ("3to5" if car_age < 5 else "over5")
            engine_type = car_update.engine_type or car.get("engine_type", "ice")
            engine_volume = car_update.engine_volume or car.get("engine_volume", 2000)
            
            calc_input = CalculatorInput(
                price_cny=car_update.price_cny,
                age=age_category,
                engine_type=engine_type,
                engine_volume=engine_volume if engine_type != "electric" else 0,
                user_type="individual",
                use_decree_140=False,
                payment_via_platform=True
            )
            calc_result = calculate_custom_price(calc_input)
            update_data["calculated_price_usd"] = calc_result.total_usd
            update_data["calculated_price_byn"] = calc_result.total_byn
        except:
            pass
    if car_update.engine_type is not None:
        update_data["engine_type"] = car_update.engine_type
    if car_update.engine_volume is not None:
        update_data["engine_volume"] = car_update.engine_volume
    if car_update.notes is not None:
        update_data["notes"] = car_update.notes
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.garage.update_one({"id": car_id}, {"$set": update_data})
    
    updated_car = await db.garage.find_one({"id": car_id}, {"_id": 0})
    return CarResponse(**updated_car)

# ==================== TENDER ENDPOINTS ====================

@api_router.post("/tenders", response_model=TenderResponse)
async def create_tender(tender: TenderCreate, current_user: dict = Depends(get_current_user)):
    car = await db.garage.find_one({"id": tender.car_id, "user_id": current_user["id"]}, {"_id": 0})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found in garage")
    
    # Update car status
    await db.garage.update_one({"id": tender.car_id}, {"$set": {"status": "tender_active"}})
    
    tender_id = str(uuid.uuid4())
    tender_doc = {
        "id": tender_id,
        "user_id": current_user["id"],
        "car_id": tender.car_id,
        "car_info": {k: v for k, v in car.items() if k not in ["_id", "user_id"]},
        "status": "active",
        "offers": [],
        "selected_offer_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenders.insert_one(tender_doc)
    
    # Generate mock offers from contractors
    mock_offers = generate_mock_offers(tender_id, car)
    await db.tenders.update_one({"id": tender_id}, {"$set": {"offers": mock_offers}})
    tender_doc["offers"] = mock_offers
    
    return TenderResponse(**tender_doc)

def generate_mock_offers(tender_id: str, car: dict) -> List[dict]:
    """Generate mock contractor offers for demonstration"""
    import random
    
    base_price = car.get("price_cny", 100000) / 7.2  # Convert to USD roughly
    contractors = [
        {"name": "AutoChina Direct", "rating": 4.9},
        {"name": "Dragon Motors", "rating": 4.7},
        {"name": "Golden Wheel Import", "rating": 4.8},
        {"name": "Pacific Auto Trade", "rating": 4.5},
        {"name": "Eastern Bridge Cars", "rating": 4.6}
    ]
    
    offers = []
    for i, contractor in enumerate(contractors[:random.randint(3, 5)]):
        variation = random.uniform(0.95, 1.08)
        offers.append({
            "id": str(uuid.uuid4()),
            "tender_id": tender_id,
            "contractor_name": contractor["name"],
            "contractor_rating": contractor["rating"],
            "price_usd": round(base_price * variation, 2),
            "delivery_days": random.randint(4, 8),
            "delivery_cost": random.choice([0, 300, 500]),
            "payment_method": random.choice(["Перевод", "Крипто", "Наличные"]),
            "status": random.choice(["Готово", "В процессе"]),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Sort by price
    offers.sort(key=lambda x: x["price_usd"])
    return offers

@api_router.get("/tenders", response_model=List[TenderResponse])
async def get_tenders(current_user: dict = Depends(get_current_user)):
    tenders = await db.tenders.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return [TenderResponse(**t) for t in tenders]

@api_router.get("/tenders/{tender_id}", response_model=TenderResponse)
async def get_tender(tender_id: str, current_user: dict = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id, "user_id": current_user["id"]}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return TenderResponse(**tender)

@api_router.post("/tenders/{tender_id}/select/{offer_id}")
async def select_offer(tender_id: str, offer_id: str, current_user: dict = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id, "user_id": current_user["id"]}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    offer_exists = any(o["id"] == offer_id for o in tender.get("offers", []))
    if not offer_exists:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    await db.tenders.update_one(
        {"id": tender_id},
        {"$set": {"selected_offer_id": offer_id, "status": "selected"}}
    )
    
    # Update car status
    await db.garage.update_one(
        {"id": tender["car_id"]},
        {"$set": {"status": "in_progress"}}
    )
    
    return {"message": "Offer selected successfully"}

# ==================== CONTRACTOR ENDPOINTS ====================

# Demo contractor data
DEMO_CONTRACTORS = [
    # Inspection companies
    {
        "id": "insp-001",
        "name": "ChinaAutoCheck",
        "contractor_type": "inspection",
        "description": "Профессиональная проверка автомобилей в Китае с выездом на место. Полный технический осмотр, проверка документов и истории авто.",
        "services": "Визуальный осмотр, диагностика ходовой, проверка ЛКП толщиномером, сканирование ошибок, проверка VIN и документов, фото/видео отчет",
        "price_range": "$150 - $300",
        "phone": "+86 138 1234 5678",
        "email": "check@chinaautocheck.com",
        "website": "https://chinaautocheck.com",
        "whatsapp": "+86 138 1234 5678",
        "wechat": "chinaautocheck",
        "telegram": "@chinaautocheck",
        "rating": 4.8,
        "deals_count": 342,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "insp-002",
        "name": "AutoExpert China",
        "contractor_type": "inspection",
        "description": "Независимая экспертиза автомобилей. Работаем по всему Китаю. Гарантия объективной оценки.",
        "services": "Полная диагностика, проверка на ДТП, юридическая чистота, оценка рыночной стоимости, онлайн-консультация",
        "price_range": "$100 - $250",
        "phone": "+86 139 8765 4321",
        "email": "info@autoexpert-china.com",
        "website": "https://autoexpert-china.com",
        "whatsapp": "+86 139 8765 4321",
        "wechat": "autoexpertcn",
        "telegram": "@autoexpertchina",
        "rating": 4.6,
        "deals_count": 218,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2024-02-15T00:00:00Z"
    },
    {
        "id": "insp-003",
        "name": "DriveCheck Pro",
        "contractor_type": "inspection",
        "description": "Быстрая и качественная проверка авто перед покупкой. Специализируемся на электромобилях и гибридах.",
        "services": "Проверка батареи EV, диагностика электросистем, тест-драйв, проверка зарядных систем",
        "price_range": "$200 - $400",
        "phone": "+86 186 5555 1234",
        "email": "pro@drivecheck.cn",
        "website": None,
        "whatsapp": "+86 186 5555 1234",
        "wechat": "drivecheckpro",
        "telegram": None,
        "rating": 4.9,
        "deals_count": 156,
        "is_verified": False,
        "logo_url": None,
        "created_at": "2024-03-20T00:00:00Z"
    },
    # Export companies
    {
        "id": "exp-001",
        "name": "SinoExport Group",
        "contractor_type": "export",
        "description": "Крупнейшая экспортная компания в Китае. Полное сопровождение сделки от покупки до отправки.",
        "services": "Выкуп авто, оформление экспортных документов, таможенное оформление в Китае, страхование груза",
        "price_range": "$500 - $1500",
        "phone": "+86 21 5888 8888",
        "email": "export@sinoexport.com",
        "website": "https://sinoexport.com",
        "whatsapp": "+86 21 5888 8888",
        "wechat": "sinoexport",
        "telegram": "@sinoexport",
        "rating": 4.7,
        "deals_count": 1250,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2023-06-01T00:00:00Z"
    },
    {
        "id": "exp-002",
        "name": "Dragon Auto Export",
        "contractor_type": "export",
        "description": "Надежный партнер для экспорта авто из Китая. Работаем с 2015 года.",
        "services": "Покупка на аукционах, переговоры с продавцом, экспортное оформление, контроль качества перед отправкой",
        "price_range": "$400 - $1200",
        "phone": "+86 755 2666 8888",
        "email": "info@dragonexport.cn",
        "website": "https://dragonexport.cn",
        "whatsapp": "+86 755 2666 8888",
        "wechat": "dragonautoexp",
        "telegram": "@dragonautoexport",
        "rating": 4.5,
        "deals_count": 890,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2023-08-15T00:00:00Z"
    },
    {
        "id": "exp-003",
        "name": "FastTrade China",
        "contractor_type": "export",
        "description": "Быстрый экспорт автомобилей. Минимальные сроки оформления документов.",
        "services": "Срочный выкуп, ускоренное оформление, VIP-сопровождение сделки",
        "price_range": "$600 - $2000",
        "phone": "+86 20 3888 6666",
        "email": "fast@fasttrade.cn",
        "website": None,
        "whatsapp": "+86 20 3888 6666",
        "wechat": "fasttradecn",
        "telegram": "@fasttradechina",
        "rating": 4.3,
        "deals_count": 445,
        "is_verified": False,
        "logo_url": None,
        "created_at": "2024-01-10T00:00:00Z"
    },
    # Logistics companies
    {
        "id": "log-001",
        "name": "EuroAsia Logistics",
        "contractor_type": "logistics",
        "description": "Международная логистика автомобилей. Доставка из Китая в Беларусь, Россию, Казахстан.",
        "services": "Морская доставка, ж/д перевозка, автовозы, страхование, отслеживание груза онлайн",
        "price_range": "$1500 - $3500",
        "phone": "+375 29 111 2233",
        "email": "logistics@euroasia-log.com",
        "website": "https://euroasia-logistics.com",
        "whatsapp": "+375 29 111 2233",
        "wechat": None,
        "telegram": "@euroasialog",
        "rating": 4.8,
        "deals_count": 2100,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2022-03-01T00:00:00Z"
    },
    {
        "id": "log-002",
        "name": "Silk Road Transport",
        "contractor_type": "logistics",
        "description": "Перевозка по Новому Шелковому пути. Оптимальное сочетание цены и скорости.",
        "services": "Контейнерные перевозки, доставка до двери, таможенное оформление в РБ, хранение на складе",
        "price_range": "$1200 - $2800",
        "phone": "+375 33 444 5566",
        "email": "info@silkroad-transport.by",
        "website": "https://silkroad-transport.by",
        "whatsapp": "+375 33 444 5566",
        "wechat": "silkroadtrans",
        "telegram": "@silkroadtransport",
        "rating": 4.6,
        "deals_count": 1560,
        "is_verified": True,
        "logo_url": None,
        "created_at": "2022-09-15T00:00:00Z"
    },
    {
        "id": "log-003",
        "name": "Belarus Auto Delivery",
        "contractor_type": "logistics",
        "description": "Специализируемся на доставке авто в Беларусь. Собственный автопарк.",
        "services": "Доставка автовозами, временное хранение, помощь в растаможке, доставка до города",
        "price_range": "$800 - $2000",
        "phone": "+375 44 777 8899",
        "email": "delivery@belauto.by",
        "website": None,
        "whatsapp": "+375 44 777 8899",
        "wechat": None,
        "telegram": "@belautodelivery",
        "rating": 4.4,
        "deals_count": 670,
        "is_verified": False,
        "logo_url": None,
        "created_at": "2023-11-20T00:00:00Z"
    },
    # Leasing companies
    {
        "id": "leas-001",
        "name": "АвтоЛизинг БЕЛ",
        "contractor_type": "leasing",
        "description": "Лидер автолизинга в Беларуси. Выгодные условия для физических и юридических лиц. Быстрое оформление.",
        "services": "Лизинг новых и б/у авто, минимальный первый взнос от 10%, срок до 7 лет, досрочное погашение без штрафов",
        "price_range": "от 8.5% годовых",
        "phone": "+375 17 336 0000",
        "email": "info@avtoleasing.by",
        "website": "https://avtoleasing.by",
        "whatsapp": "+375 29 336 0000",
        "wechat": None,
        "telegram": "@avtoleasingby",
        "rating": 4.9,
        "deals_count": 3500,
        "is_verified": True,
        "logo_url": None,
        "leasing_rate": 8.5,
        "min_down_payment": 10,
        "max_term_months": 84,
        "created_at": "2020-01-15T00:00:00Z"
    },
    {
        "id": "leas-002",
        "name": "ПромЛизинг",
        "contractor_type": "leasing",
        "description": "Надежный партнер для бизнеса. Специальные условия для корпоративных клиентов и автопарков.",
        "services": "Корпоративный лизинг, возвратный лизинг, лизинг электромобилей, страхование КАСКО в подарок",
        "price_range": "от 9.0% годовых",
        "phone": "+375 17 299 8800",
        "email": "leasing@promleasing.by",
        "website": "https://promleasing.by",
        "whatsapp": "+375 29 299 8800",
        "wechat": None,
        "telegram": "@promleasingby",
        "rating": 4.7,
        "deals_count": 2800,
        "is_verified": True,
        "logo_url": None,
        "leasing_rate": 9.0,
        "min_down_payment": 15,
        "max_term_months": 60,
        "created_at": "2019-06-01T00:00:00Z"
    },
    {
        "id": "leas-003",
        "name": "СмартЛиз",
        "contractor_type": "leasing",
        "description": "Современный подход к лизингу. Онлайн-оформление за 1 день. Гибкие условия.",
        "services": "Экспресс-лизинг, онлайн заявка, одобрение за 2 часа, без справок о доходах",
        "price_range": "от 10.5% годовых",
        "phone": "+375 44 555 1234",
        "email": "hello@smartlease.by",
        "website": "https://smartlease.by",
        "whatsapp": "+375 44 555 1234",
        "wechat": None,
        "telegram": "@smartleaseby",
        "rating": 4.5,
        "deals_count": 1200,
        "is_verified": False,
        "logo_url": None,
        "leasing_rate": 10.5,
        "min_down_payment": 20,
        "max_term_months": 48,
        "created_at": "2022-03-10T00:00:00Z"
    }
]

@api_router.get("/contractors", response_model=List[ContractorResponse])
async def get_contractors(contractor_type: Optional[str] = None):
    """Get all contractors, optionally filtered by type"""
    # Get verified contractors from database
    query = {"status": "approved", "verified": True}
    
    db_contractors = await db.contractors.find(query, {"_id": 0, "password_hash": 0}).to_list(100)
    
    # Filter by service type if specified
    if contractor_type:
        filtered_db = []
        for c in db_contractors:
            services = c.get("services", [])
            # services can be string or list
            if isinstance(services, str):
                services = [s.strip() for s in services.split(",")]
            if contractor_type in services or c.get("contractor_type") == contractor_type:
                # Map to expected format
                c["contractor_type"] = contractor_type
                c["name"] = c.get("name") or c.get("company_name")
                c["services"] = ", ".join(services) if isinstance(services, list) else services
                filtered_db.append(c)
        db_contractors = filtered_db
    else:
        # Add name field from company_name if missing
        for c in db_contractors:
            c["name"] = c.get("name") or c.get("company_name")
            services = c.get("services", [])
            if isinstance(services, list):
                c["services"] = ", ".join(services)
    
    # Combine with demo data (if not already in DB)
    demo_ids = {c["id"] for c in db_contractors}
    demo_emails = {c.get("email") for c in db_contractors if c.get("email")}
    demo_filtered = [c for c in DEMO_CONTRACTORS if c["id"] not in demo_ids and c.get("email") not in demo_emails]
    
    if contractor_type:
        demo_filtered = [c for c in demo_filtered if c["contractor_type"] == contractor_type]
    
    all_contractors = db_contractors + demo_filtered
    
    # Sort by verified status, rating and deals count
    all_contractors.sort(key=lambda x: (-x.get("verified", False), -x.get("is_verified", False), -x.get("rating", 0), -x.get("deals_count", 0)))
    
    return all_contractors

@api_router.get("/contractors/{contractor_id}", response_model=ContractorResponse)
async def get_contractor(contractor_id: str):
    """Get contractor by ID"""
    # Check database first
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if contractor:
        return contractor
    
    # Check demo data
    for c in DEMO_CONTRACTORS:
        if c["id"] == contractor_id:
            return c
    
    raise HTTPException(status_code=404, detail="Contractor not found")

@api_router.post("/contractors", response_model=ContractorResponse)
async def create_contractor(contractor: ContractorCreate, current_user: dict = Depends(get_current_user)):
    """Create a new contractor (admin only)"""
    contractor_id = str(uuid.uuid4())
    contractor_data = {
        "id": contractor_id,
        **contractor.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contractors.insert_one(contractor_data)
    contractor_data.pop("_id", None)
    return ContractorResponse(**contractor_data)

@api_router.delete("/contractors/{contractor_id}")
async def delete_contractor(contractor_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a contractor"""
    # Can't delete demo contractors, only database ones
    result = await db.contractors.delete_one({"id": contractor_id})
    if result.deleted_count == 0:
        # Check if it's a demo contractor
        for c in DEMO_CONTRACTORS:
            if c["id"] == contractor_id:
                raise HTTPException(status_code=400, detail="Cannot delete demo contractor")
        raise HTTPException(status_code=404, detail="Contractor not found")
    return {"message": "Contractor deleted"}

@api_router.post("/garage/{car_id}/assign-contractor")
async def assign_contractor_to_car(
    car_id: str, 
    assignment: ContractorAssignment,
    current_user: dict = Depends(get_current_user)
):
    """Assign a contractor to a car for a specific stage"""
    # Verify car belongs to user
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Verify contractor exists
    contractor = await db.contractors.find_one({"id": assignment.contractor_id}, {"_id": 0})
    if not contractor:
        # Check demo data
        contractor = next((c for c in DEMO_CONTRACTORS if c["id"] == assignment.contractor_id), None)
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # Update car with contractor assignment
    update_field = f"contractors.{assignment.stage}"
    await db.garage.update_one(
        {"id": car_id},
        {"$set": {
            update_field: {
                "contractor_id": assignment.contractor_id,
                "contractor_name": contractor["name"],
                "assigned_at": datetime.now(timezone.utc).isoformat()
            }
        }}
    )
    
    return {"message": f"Contractor assigned to {assignment.stage} stage"}

@api_router.delete("/garage/{car_id}/contractor/{stage}")
async def remove_contractor_from_car(
    car_id: str,
    stage: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove contractor assignment from a car"""
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    update_field = f"contractors.{stage}"
    await db.garage.update_one(
        {"id": car_id},
        {"$unset": {update_field: ""}}
    )
    
    return {"message": f"Contractor removed from {stage} stage"}

# ==================== LEASING CALCULATOR ====================

class LeasingCalculation(BaseModel):
    car_price_usd: float
    down_payment_percent: float
    term_months: int
    leasing_company_id: Optional[str] = None

@api_router.post("/leasing/calculate")
async def calculate_leasing(data: LeasingCalculation):
    """Calculate leasing payments"""
    # Get leasing rate from company or use default
    rate = 9.0  # Default annual rate
    
    if data.leasing_company_id:
        for c in DEMO_CONTRACTORS:
            if c["id"] == data.leasing_company_id and c.get("leasing_rate"):
                rate = c["leasing_rate"]
                break
    
    # Calculate
    down_payment = data.car_price_usd * (data.down_payment_percent / 100)
    financed_amount = data.car_price_usd - down_payment
    
    # Monthly rate
    monthly_rate = rate / 100 / 12
    
    # Monthly payment (annuity formula)
    if monthly_rate > 0:
        monthly_payment = financed_amount * (monthly_rate * (1 + monthly_rate)**data.term_months) / ((1 + monthly_rate)**data.term_months - 1)
    else:
        monthly_payment = financed_amount / data.term_months
    
    # First payment = down payment + first monthly
    first_payment = down_payment + monthly_payment
    
    # Total cost
    total_cost = down_payment + (monthly_payment * data.term_months)
    overpayment = total_cost - data.car_price_usd
    
    return {
        "car_price_usd": data.car_price_usd,
        "down_payment": round(down_payment, 2),
        "down_payment_percent": data.down_payment_percent,
        "financed_amount": round(financed_amount, 2),
        "term_months": data.term_months,
        "annual_rate": rate,
        "monthly_payment": round(monthly_payment, 2),
        "first_payment": round(first_payment, 2),
        "total_cost": round(total_cost, 2),
        "overpayment": round(overpayment, 2)
    }

# ==================== MANAGER HELP REQUEST ====================

MANAGER_HELP_COST = 200  # USD

@api_router.post("/garage/{car_id}/request-manager-help")
async def request_manager_help(car_id: str, current_user: dict = Depends(get_current_user)):
    """Request manager help for car selection ($200)"""
    car = await db.garage.find_one({"id": car_id, "user_id": current_user["id"]})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Check user balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < MANAGER_HELP_COST:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно средств. Требуется ${MANAGER_HELP_COST}, на балансе ${balance}"
        )
    
    # Deduct from balance
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -MANAGER_HELP_COST}}
    )
    
    # Create help request
    request_id = str(uuid.uuid4())
    help_request = {
        "id": request_id,
        "user_id": current_user["id"],
        "car_id": car_id,
        "type": "manager_help",
        "cost": MANAGER_HELP_COST,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.help_requests.insert_one(help_request)
    
    # Update car status
    await db.garage.update_one(
        {"id": car_id},
        {"$set": {"manager_help_requested": True, "manager_help_request_id": request_id}}
    )
    
    return {
        "message": "Запрос на помощь менеджера отправлен",
        "request_id": request_id,
        "cost": MANAGER_HELP_COST,
        "new_balance": balance - MANAGER_HELP_COST
    }

# ==================== HOT DEALS ENDPOINTS ====================

@api_router.get("/hot-deals", response_model=List[HotDealResponse])
async def get_hot_deals(limit: int = 10, active_only: bool = True):
    """Get hot deals, optionally filtering expired ones"""
    query = {}
    if active_only:
        query["expires_at"] = {"$gt": datetime.now(timezone.utc).isoformat()}
    
    deals = await db.hot_deals.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Auto-delete expired deals
    await db.hot_deals.delete_many({"expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}})
    
    return deals

@api_router.get("/hot-deals/{deal_id}", response_model=HotDealResponse)
async def get_hot_deal(deal_id: str):
    """Get a specific hot deal"""
    deal = await db.hot_deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Предложение не найдено")
    
    # Check if expired
    if deal.get("expires_at") and deal["expires_at"] < datetime.now(timezone.utc).isoformat():
        await db.hot_deals.delete_one({"id": deal_id})
        raise HTTPException(status_code=404, detail="Предложение истекло")
    
    return deal

@api_router.post("/hot-deals", response_model=HotDealResponse)
async def create_hot_deal(deal: HotDealCreate, current_user: dict = Depends(get_current_user)):
    """Create a new hot deal - only moderators and verified contractors"""
    user_role = current_user.get("role", "user")
    
    # Check if user is moderator/admin or verified contractor
    is_moderator = user_role in ["moderator", "admin"]
    
    # Check if user is a verified contractor
    contractor = await db.contractors.find_one({
        "email": current_user["email"],
        "is_verified": True
    })
    is_verified_contractor = contractor is not None
    
    if not is_moderator and not is_verified_contractor:
        raise HTTPException(
            status_code=403, 
            detail="Только модераторы и верифицированные подрядчики могут создавать горящие предложения"
        )
    
    # Calculate price for Belarus
    calc_result = None
    try:
        current_year = datetime.now().year
        car_age = current_year - deal.year
        age_category = "under3" if car_age < 3 else ("3to5" if car_age < 5 else "over5")
        
        calc_input = CalculatorInput(
            price_cny=deal.special_price_cny or deal.price_cny,
            age=age_category,
            engine_type=deal.engine_type,
            engine_volume=deal.engine_volume or 2000,
            user_type="individual",
            use_decree_140=False,
            payment_via_platform=True
        )
        # Use calculator logic directly
        # ... simplified calculation
        cny_rate = 12.5  # Approximate CNY to USD
        calculated_price_usd = (deal.special_price_cny or deal.price_cny) / cny_rate * 1.3  # +30% for customs etc
    except:
        calculated_price_usd = None
    
    deal_id = str(uuid.uuid4())
    seller_name = contractor["name"] if is_verified_contractor else current_user["name"]
    seller_type = "contractor" if is_verified_contractor else "moderator"
    
    new_deal = {
        "id": deal_id,
        "brand": deal.brand,
        "model": deal.model,
        "year": deal.year,
        "price_cny": deal.price_cny,
        "special_price_cny": deal.special_price_cny,
        "calculated_price_usd": round(calculated_price_usd, 2) if calculated_price_usd else None,
        "mileage": deal.mileage,
        "engine_type": deal.engine_type,
        "engine_volume": deal.engine_volume,
        "image_url": deal.image_url,
        "description": deal.description,
        "expires_at": deal.expires_at,
        "seller_id": contractor["id"] if is_verified_contractor else current_user["id"],
        "seller_name": seller_name,
        "seller_type": seller_type,
        "is_verified_seller": is_verified_contractor or is_moderator,
        "contact_info": deal.contact_info,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.hot_deals.insert_one(new_deal)
    
    # Return without _id
    del new_deal["contact_info"]  # Don't expose in response
    return new_deal

@api_router.delete("/hot-deals/{deal_id}")
async def delete_hot_deal(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a hot deal - only owner or admin"""
    deal = await db.hot_deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Предложение не найдено")
    
    user_role = current_user.get("role", "user")
    is_admin = user_role in ["moderator", "admin"]
    is_owner = deal.get("seller_id") == current_user["id"]
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Нет прав на удаление")
    
    await db.hot_deals.delete_one({"id": deal_id})
    return {"message": "Предложение удалено"}

@api_router.post("/hot-deals/seed-demo")
async def seed_demo_hot_deals():
    """Seed demo hot deals for testing"""
    # Check if already have deals
    existing = await db.hot_deals.count_documents({})
    if existing > 0:
        return {"message": "Demo deals already exist", "count": existing}
    
    demo_deals = [
        {
            "id": "hot-001",
            "brand": "BYD",
            "model": "Seal",
            "year": 2024,
            "price_cny": 219800,
            "special_price_cny": 189800,
            "calculated_price_usd": 28500,
            "mileage": 5000,
            "engine_type": "electric",
            "engine_volume": None,
            "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
            "description": "Срочная продажа! Электромобиль в идеальном состоянии, на гарантии.",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
            "seller_id": "exp-001",
            "seller_name": "GlobalAutoExport",
            "seller_type": "contractor",
            "is_verified_seller": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "hot-002",
            "brand": "Zeekr",
            "model": "001",
            "year": 2023,
            "price_cny": 289000,
            "special_price_cny": 259000,
            "calculated_price_usd": 38900,
            "mileage": 12000,
            "engine_type": "electric",
            "engine_volume": None,
            "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
            "description": "Премиальный электрокроссовер Zeekr. Полная комплектация.",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "seller_id": "exp-002",
            "seller_name": "ChinaMotors Direct",
            "seller_type": "contractor",
            "is_verified_seller": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "hot-003",
            "brand": "GEELY",
            "model": "Monjaro",
            "year": 2024,
            "price_cny": 178000,
            "special_price_cny": 158000,
            "calculated_price_usd": 23700,
            "mileage": 3000,
            "engine_type": "hybrid",
            "engine_volume": 2000,
            "image_url": "https://customer-assets.emergentagent.com/job_china-motors-by/artifacts/os4c665q_GEELY%20MANJARO.jpg",
            "description": "Новый гибридный кроссовер от Geely. Выгодное предложение!",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat(),
            "seller_id": "exp-001",
            "seller_name": "GlobalAutoExport",
            "seller_type": "contractor",
            "is_verified_seller": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "hot-004",
            "brand": "Li Auto",
            "model": "L7",
            "year": 2024,
            "price_cny": 339800,
            "special_price_cny": 309800,
            "calculated_price_usd": 46500,
            "mileage": 8000,
            "engine_type": "hybrid",
            "engine_volume": 1500,
            "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
            "description": "Премиальный гибридный внедорожник с запасом хода 1000+ км.",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=36)).isoformat(),
            "seller_id": "exp-002",
            "seller_name": "ChinaMotors Direct",
            "seller_type": "contractor",
            "is_verified_seller": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.hot_deals.insert_many(demo_deals)
    return {"message": "Demo hot deals created", "count": len(demo_deals)}

@api_router.post("/hot-deals/{deal_id}/add-to-garage")
async def add_hot_deal_to_garage(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Add a hot deal car to user's garage with seller pre-selected"""
    deal = await db.hot_deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Предложение не найдено")
    
    # Check if expired
    if deal.get("expires_at") and deal["expires_at"] < datetime.now(timezone.utc).isoformat():
        await db.hot_deals.delete_one({"id": deal_id})
        raise HTTPException(status_code=404, detail="Предложение истекло")
    
    # Create car in garage
    car_id = str(uuid.uuid4())
    
    # Get seller contractor info if seller is a contractor
    seller_contractor = None
    if deal.get("seller_type") == "contractor":
        seller_contractor = await db.contractors.find_one({"id": deal.get("seller_id")}, {"_id": 0})
    
    new_car = {
        "id": car_id,
        "user_id": current_user["id"],
        "brand": deal["brand"],
        "model": deal["model"],
        "year": deal["year"],
        "price_cny": deal.get("special_price_cny") or deal["price_cny"],
        "engine_type": deal.get("engine_type", "ice"),
        "engine_volume": deal.get("engine_volume"),
        "mileage": deal.get("mileage"),
        "image_url": deal.get("image_url"),
        "source_url": None,
        "description": deal.get("description"),
        "calculated_price_usd": deal.get("calculated_price_usd"),
        "calculated_price_byn": deal.get("calculated_price_usd", 0) * 3.2 if deal.get("calculated_price_usd") else None,
        "status": "saved",
        "from_hot_deal": True,
        "hot_deal_id": deal_id,
        "contractors": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Auto-assign seller as contractor if they're a verified contractor
    if seller_contractor:
        # Determine contractor type to assign
        contractor_type = seller_contractor.get("contractor_type", "export")
        if contractor_type in ["inspection", "export", "logistics", "leasing"]:
            new_car["contractors"][contractor_type] = {
                "contractor_id": seller_contractor["id"],
                "contractor_name": seller_contractor["name"],
                "assigned_at": datetime.now(timezone.utc).isoformat()
            }
    
    await db.garage.insert_one(new_car)
    
    return {
        "message": "Автомобиль добавлен в гараж",
        "car_id": car_id,
        "seller_assigned": seller_contractor is not None,
        "seller_name": deal.get("seller_name")
    }

# ==================== CONTRACTOR APPLICATIONS ENDPOINTS ====================

class ContractorApplicationCreate(BaseModel):
    company_name: str
    contractor_type: str
    registration_number: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    contact_person: str
    position: Optional[str] = None
    phone: str
    email: str
    whatsapp: Optional[str] = None
    wechat: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None
    description: str
    services: str
    price_range: Optional[str] = None
    experience_years: Optional[int] = 0
    deals_completed: Optional[int] = 0
    license_info: Optional[str] = None
    additional_info: Optional[str] = None

@api_router.post("/contractor-applications")
async def create_contractor_application(application: ContractorApplicationCreate):
    """Submit a new contractor application (public endpoint)"""
    app_id = str(uuid.uuid4())
    app_data = {
        "id": app_id,
        **application.model_dump(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewed_by": None
    }
    await db.contractor_applications.insert_one(app_data)
    return {"message": "Application submitted successfully", "application_id": app_id}

# ==================== MODERATOR ENDPOINTS ====================

@api_router.get("/moderator/applications")
async def get_contractor_applications(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all contractor applications (moderator only)"""
    applications = await db.contractor_applications.find({}, {"_id": 0}).to_list(100)
    return applications

@api_router.post("/moderator/applications/{app_id}/approve")
async def approve_contractor_application(app_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Approve a contractor application"""
    application = await db.contractor_applications.find_one({"id": app_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Create contractor from application
    contractor_id = str(uuid.uuid4())
    contractor_data = {
        "id": contractor_id,
        "name": application["company_name"],
        "contractor_type": application["contractor_type"],
        "description": application["description"],
        "services": application["services"],
        "price_range": application.get("price_range"),
        "phone": application["phone"],
        "email": application["email"],
        "website": application.get("website"),
        "whatsapp": application.get("whatsapp"),
        "wechat": application.get("wechat"),
        "telegram": application.get("telegram"),
        "rating": 5.0,
        "deals_count": application.get("deals_completed", 0),
        "is_verified": True,
        "logo_url": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contractors.insert_one(contractor_data)
    
    # Update application status
    await db.contractor_applications.update_one(
        {"id": app_id},
        {"$set": {
            "status": "approved",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": current_user["id"]
        }}
    )
    
    return {"message": "Application approved", "contractor_id": contractor_id}

@api_router.post("/moderator/applications/{app_id}/reject")
async def reject_contractor_application(app_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Reject a contractor application"""
    result = await db.contractor_applications.update_one(
        {"id": app_id},
        {"$set": {
            "status": "rejected",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": current_user["id"]
        }}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application rejected"}

@api_router.get("/moderator/deals")
async def get_all_deals(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all deals for moderator view"""
    # Get all garage items that have tenders or are in progress
    deals = await db.garage.find(
        {"status": {"$in": ["tender_active", "in_progress"]}},
        {"_id": 0}
    ).to_list(100)
    
    result = []
    for deal in deals:
        # Get user info
        user = await db.users.find_one({"id": deal["user_id"]}, {"_id": 0})
        result.append({
            "id": deal["id"],
            "car_brand": deal["brand"],
            "car_model": deal["model"],
            "client_name": user.get("name", "Unknown") if user else "Unknown",
            "amount": deal.get("calculated_price_usd", 0),
            "current_stage": deal.get("current_stage", "inspection"),
            "completed_stages": deal.get("completed_stages", []),
            "status": deal["status"]
        })
    
    return result

@api_router.post("/moderator/deals/{deal_id}/confirm-stage")
async def confirm_deal_stage(deal_id: str, stage: dict, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Confirm a stage of a deal"""
    stage_name = stage.get("stage")
    if not stage_name:
        raise HTTPException(status_code=400, detail="Stage name required")
    
    deal = await db.garage.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    completed_stages = deal.get("completed_stages", [])
    if stage_name not in completed_stages:
        completed_stages.append(stage_name)
    
    # Determine next stage
    stages_order = ["inspection", "export", "logistics", "customs", "delivery"]
    current_idx = stages_order.index(stage_name) if stage_name in stages_order else 0
    next_stage = stages_order[current_idx + 1] if current_idx + 1 < len(stages_order) else "completed"
    
    await db.garage.update_one(
        {"id": deal_id},
        {"$set": {
            "completed_stages": completed_stages,
            "current_stage": next_stage,
            "status": "completed" if next_stage == "completed" else "in_progress"
        }}
    )
    
    return {"message": f"Stage {stage_name} confirmed"}

@api_router.get("/moderator/tenders")
async def get_all_tenders_moderator(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all tenders for moderator"""
    tenders = await db.tenders.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for tender in tenders:
        car = await db.garage.find_one({"id": tender["car_id"]}, {"_id": 0})
        result.append({
            "id": tender["id"],
            "brand": car["brand"] if car else "Unknown",
            "model": car["model"] if car else "Unknown",
            "budget": car.get("calculated_price_usd", 0) if car else 0,
            "offers_count": len(tender.get("offers", [])),
            "status": tender["status"],
            "created_at": tender["created_at"]
        })
    
    return result

class ModeratorTenderCreate(BaseModel):
    brand: str
    model: str
    budget: Optional[str] = None

@api_router.post("/moderator/tenders")
async def create_tender_by_moderator(tender_data: ModeratorTenderCreate, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Create a new tender by moderator (independent of client)"""
    # Create a virtual car entry
    car_id = str(uuid.uuid4())
    car_doc = {
        "id": car_id,
        "user_id": "moderator",
        "brand": tender_data.brand,
        "model": tender_data.model,
        "year": datetime.now().year,
        "price_cny": 0,
        "engine_type": "electric",
        "calculated_price_usd": float(tender_data.budget) if tender_data.budget else 0,
        "status": "tender_active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.garage.insert_one(car_doc)
    
    # Create tender
    tender_id = str(uuid.uuid4())
    tender_doc = {
        "id": tender_id,
        "user_id": "moderator",
        "car_id": car_id,
        "status": "active",
        "offers": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by_moderator": True
    }
    await db.tenders.insert_one(tender_doc)
    
    return {"message": "Tender created", "tender_id": tender_id}

# ==================== DOCUMENTS ENDPOINTS ====================

@api_router.post("/documents", response_model=DocumentResponse)
async def create_document(doc: DocumentCreate, current_user: dict = Depends(get_current_user)):
    doc_id = str(uuid.uuid4())
    doc_data = {
        "id": doc_id,
        "user_id": current_user["id"],
        **doc.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.documents.insert_one(doc_data)
    return DocumentResponse(**doc_data)

@api_router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(current_user: dict = Depends(get_current_user)):
    docs = await db.documents.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return [DocumentResponse(**d) for d in docs]

# ==================== CALCULATOR ENDPOINT ====================

# Exchange rates cache
exchange_rates_cache = {"rates": None, "updated": None}

async def get_exchange_rates():
    """Fetch exchange rates or use cached values"""
    now = datetime.now(timezone.utc)
    
    if exchange_rates_cache["rates"] and exchange_rates_cache["updated"]:
        cache_age = (now - exchange_rates_cache["updated"]).total_seconds()
        if cache_age < 3600:  # Cache for 1 hour
            return exchange_rates_cache["rates"]
    
    # Default rates if API fails
    default_rates = {"CNY_EUR": 0.127, "CNY_USD": 0.138, "USD_BYN": 3.25, "EUR_BYN": 3.55}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to get rates from NBRB API
            response = await client.get("https://api.nbrb.by/exrates/rates?periodicity=0")
            if response.status_code == 200:
                data = response.json()
                rates = {}
                for item in data:
                    if item["Cur_Abbreviation"] == "USD":
                        rates["USD_BYN"] = item["Cur_OfficialRate"]
                    elif item["Cur_Abbreviation"] == "EUR":
                        rates["EUR_BYN"] = item["Cur_OfficialRate"]
                    elif item["Cur_Abbreviation"] == "CNY":
                        rates["CNY_BYN"] = item["Cur_OfficialRate"] / item.get("Cur_Scale", 1)
                
                if "CNY_BYN" in rates and "EUR_BYN" in rates:
                    rates["CNY_EUR"] = rates["CNY_BYN"] / rates["EUR_BYN"]
                if "CNY_BYN" in rates and "USD_BYN" in rates:
                    rates["CNY_USD"] = rates["CNY_BYN"] / rates["USD_BYN"]
                
                if rates:
                    exchange_rates_cache["rates"] = {**default_rates, **rates}
                    exchange_rates_cache["updated"] = now
                    return exchange_rates_cache["rates"]
    except Exception as e:
        logger.error(f"Failed to fetch exchange rates: {e}")
    
    return default_rates

@api_router.post("/calculator", response_model=CalculatorResult)
async def calculate_customs(data: CalculatorInput):
    rates = await get_exchange_rates()
    
    price_eur = data.price_cny * rates["CNY_EUR"]
    price_usd = data.price_cny * rates["CNY_USD"]
    
    # Fixed costs in BYN
    customs_fee_byn = 120  # Таможенный сбор
    warehouse_fee_byn = 350  # Услуги склада и декларантов
    epts_fee_byn = 70  # ЭПТС
    
    # Fixed costs in USD
    delivery_usd = 2300  # Доставка до Беларуси
    exporter_commission_usd = 900  # Комиссия экспортера
    china_processing_cny = 9000  # Услуги в Китае
    china_processing_usd = china_processing_cny * rates["CNY_USD"]
    
    fixed_costs_usd = delivery_usd + exporter_commission_usd + china_processing_usd
    fixed_costs_byn = customs_fee_byn + warehouse_fee_byn + epts_fee_byn
    
    customs_duty = 0
    utilization_fee = 0
    vat = 0
    
    if data.user_type == "individual":
        # ФИЗИЧЕСКИЕ ЛИЦА
        if data.engine_type == "electric":
            customs_duty = 0
            utilization_fee = 544.5 if data.age == "under3" else 1089
        elif data.engine_type == "hybrid":
            customs_duty = price_eur * 0.15
            vat = (price_eur + customs_duty) * 0.20
            utilization_fee = 544.5 if data.age == "under3" else 1089
        else:
            # ДВС
            volume = data.engine_volume or 2000
            
            if data.age == "under3":
                # До 3 лет - процент от стоимости
                if price_eur <= 8500:
                    rate_pct, rate_per_cc = 0.54, 2.5
                elif price_eur <= 16700:
                    rate_pct, rate_per_cc = 0.48, 3.5
                elif price_eur <= 42300:
                    rate_pct, rate_per_cc = 0.48, 5.5
                elif price_eur <= 84500:
                    rate_pct, rate_per_cc = 0.48, 7.5
                elif price_eur <= 169000:
                    rate_pct, rate_per_cc = 0.48, 15
                else:
                    rate_pct, rate_per_cc = 0.48, 20
                
                duty_by_pct = price_eur * rate_pct
                duty_by_volume = volume * rate_per_cc
                customs_duty = max(duty_by_pct, duty_by_volume)
                utilization_fee = 544.5
                
            elif data.age == "3to5":
                # 3-5 лет - только по объему
                if volume <= 1000:
                    rate = 1.5
                elif volume <= 1500:
                    rate = 1.7
                elif volume <= 1800:
                    rate = 2.5
                elif volume <= 2300:
                    rate = 2.7
                elif volume <= 3000:
                    rate = 3.0
                else:
                    rate = 3.6
                customs_duty = volume * rate
                utilization_fee = 1089
                
            else:  # over5
                if volume <= 1000:
                    rate = 3.0
                elif volume <= 1500:
                    rate = 3.2
                elif volume <= 1800:
                    rate = 3.5
                elif volume <= 2300:
                    rate = 4.8
                elif volume <= 3000:
                    rate = 5.0
                else:
                    rate = 5.7
                customs_duty = volume * rate
                utilization_fee = 1089
    
    else:
        # ЮРИДИЧЕСКИЕ ЛИЦА
        volume = data.engine_volume or 2000
        
        if data.engine_type == "electric":
            customs_duty = 0
            utilization_fee = 1148.86 if data.age == "under3" else 2757.36
        else:
            # Утиль сбор для юр лиц по объему
            if data.age == "under3":
                if data.engine_type == "electric":
                    utilization_fee = 1148.86
                elif volume <= 1000:
                    utilization_fee = 6365.57
                elif volume <= 2000:
                    utilization_fee = 23575.91
                elif volume <= 3000:
                    utilization_fee = 66248.51
                elif volume <= 3500:
                    utilization_fee = 76068.86
                else:
                    utilization_fee = 96868.22
            else:
                if data.engine_type == "electric":
                    utilization_fee = 2757.36
                elif volume <= 1000:
                    utilization_fee = 16249.5
                elif volume <= 2000:
                    utilization_fee = 41471.55
                elif volume <= 3000:
                    utilization_fee = 100301.81
                elif volume <= 3500:
                    utilization_fee = 116459.46
                else:
                    utilization_fee = 116459.46
            
            # Таможенная пошлина
            if data.age == "under3":
                if volume <= 3000:
                    customs_duty = price_eur * 0.15
                else:
                    duty_by_pct = price_eur * 0.23
                    duty_by_volume = volume * 1.57
                    customs_duty = max(duty_by_pct, duty_by_volume)
            else:
                # 3+ лет
                if volume <= 1000:
                    rate_pct, rate_per_cc = 0.20, 0.36
                elif volume <= 1500:
                    rate_pct, rate_per_cc = 0.20, 0.40
                elif volume <= 1800:
                    rate_pct, rate_per_cc = 0.20, 0.36
                elif volume <= 2300:
                    rate_pct, rate_per_cc = 0.20, 0.44
                elif volume <= 3000:
                    rate_pct, rate_per_cc = 0.20, 0.44
                else:
                    rate_pct, rate_per_cc = 0.20, 0.80
                
                duty_by_pct = price_eur * rate_pct
                duty_by_volume = volume * rate_per_cc
                customs_duty = max(duty_by_pct, duty_by_volume)
        
        # НДС для юр лиц
        vat = (price_eur + customs_duty) * 0.20
    
    # Convert customs duty from EUR to BYN
    customs_duty_byn = customs_duty * rates.get("EUR_BYN", 3.55)
    vat_byn = vat * rates.get("EUR_BYN", 3.55)
    
    # Total calculations
    total_byn = (
        data.price_cny * rates.get("CNY_BYN", rates["CNY_USD"] * rates["USD_BYN"]) +
        customs_duty_byn +
        utilization_fee +
        vat_byn +
        fixed_costs_byn +
        fixed_costs_usd * rates["USD_BYN"]
    )
    
    total_usd = total_byn / rates["USD_BYN"]
    
    # Комиссия платформы 3% от стоимости авто в USD
    platform_commission_usd = price_usd * 0.03
    platform_commission_byn = platform_commission_usd * rates["USD_BYN"]
    
    # Комиссия за оплату 1.5% (через платформу или банк - одинаково)
    payment_commission_usd = price_usd * 0.015
    payment_commission_byn = payment_commission_usd * rates["USD_BYN"]
    
    # Применение льготы по Указу 140 (50% скидка на таможенные пошлины и налоги)
    decree_140_discount_byn = 0
    if data.user_type == "individual" and data.use_decree_140:
        # Скидка 50% на таможенную пошлину и НДС
        discount_on_duty = customs_duty_byn * 0.5
        discount_on_vat = vat_byn * 0.5
        decree_140_discount_byn = discount_on_duty + discount_on_vat
        customs_duty_byn = customs_duty_byn - discount_on_duty
        vat_byn = vat_byn - discount_on_vat
    
    # Пересчет итога с учетом льготы и комиссий
    total_byn = (
        data.price_cny * rates.get("CNY_BYN", rates["CNY_USD"] * rates["USD_BYN"]) +
        customs_duty_byn +
        utilization_fee +
        vat_byn +
        fixed_costs_byn +
        fixed_costs_usd * rates["USD_BYN"] +
        platform_commission_byn +
        payment_commission_byn
    )
    
    total_usd = total_byn / rates["USD_BYN"]
    
    breakdown = {
        "car_price_cny": data.price_cny,
        "car_price_eur": round(price_eur, 2),
        "car_price_usd": round(price_usd, 2),
        "customs_duty_eur": round(customs_duty, 2),
        "customs_duty_byn": round(customs_duty_byn, 2),
        "utilization_fee_byn": round(utilization_fee, 2),
        "vat_eur": round(vat, 2),
        "vat_byn": round(vat_byn, 2),
        "fixed_byn": round(fixed_costs_byn, 2),
        "fixed_usd": round(fixed_costs_usd, 2),
        "platform_commission_usd": round(platform_commission_usd, 2),
        "platform_commission_byn": round(platform_commission_byn, 2),
        "payment_commission_usd": round(payment_commission_usd, 2),
        "payment_commission_byn": round(payment_commission_byn, 2),
        "decree_140_discount_byn": round(decree_140_discount_byn, 2),
        "decree_140_applied": data.use_decree_140 and data.user_type == "individual",
        "exchange_rates": rates
    }
    
    return CalculatorResult(
        price_cny=data.price_cny,
        price_eur=round(price_eur, 2),
        price_usd=round(price_usd, 2),
        customs_duty=round(customs_duty_byn, 2),
        utilization_fee=round(utilization_fee, 2),
        vat=round(vat_byn, 2),
        fixed_costs_byn=round(fixed_costs_byn, 2),
        fixed_costs_usd=round(fixed_costs_usd, 2),
        platform_commission=round(platform_commission_byn, 2),
        payment_commission=round(payment_commission_byn, 2),
        decree_140_discount=round(decree_140_discount_byn, 2),
        total_byn=round(total_byn, 2),
        total_usd=round(total_usd, 2),
        breakdown=breakdown
    )

@api_router.get("/exchange-rates")
async def get_rates():
    return await get_exchange_rates()

# ==================== AI CHAT ENDPOINT ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    session_id = message.session_id or str(uuid.uuid4())
    
    system_message = """Ты - AI-ассистент платформы CARBRIDGE, помогающий клиентам с подбором автомобилей из Китая.

Твои задачи:
1. Помогать определить потребности клиента (бюджет, тип кузова, новый/с пробегом, год, привод, приоритеты)
2. Рекомендовать подходящие модели китайских автомобилей (BYD, Geely, Chery, Li Auto, NIO, Haval, Changan и др.)
3. Объяснять процесс покупки и доставки авто из Китая
4. Консультировать по растаможке и документам
5. Отвечать на вопросы о платформе CARBRIDGE

Основные площадки для поиска авто в Китае:
- che168.com - крупнейшая площадка
- autohome.com.cn - популярный автопортал
- taoche.com - проверенные дилеры
- guazi.com - авто с пробегом

При общении будь дружелюбным, профессиональным и информативным. Отвечай на русском языке.
Если клиент готов к покупке, предложи ему добавить авто в гараж и отправить запрос на тендер."""

    try:
        # Get chat history from database
        history = await db.chat_history.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(20)
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Add history to chat context
        for h in history:
            if h["role"] == "user":
                await chat.send_message(UserMessage(text=h["content"]))
            # Assistant messages are already in context from previous send_message calls
        
        user_msg = UserMessage(text=message.message)
        response = await chat.send_message(user_msg)
        
        # Save to history
        timestamp = datetime.now(timezone.utc).isoformat()
        await db.chat_history.insert_many([
            {"session_id": session_id, "role": "user", "content": message.message, "timestamp": timestamp},
            {"session_id": session_id, "role": "assistant", "content": response, "timestamp": timestamp}
        ])
        
        return ChatResponse(response=response, session_id=session_id)
        
    except Exception as e:
        logger.error(f"AI Chat error: {e}")
        # Fallback response
        fallback = """Извините, AI-ассистент временно недоступен. 

Вы можете:
1. Использовать калькулятор для расчета стоимости авто
2. Перейти на площадки che168.com или autohome.com.cn для поиска авто
3. Добавить авто в гараж и отправить запрос на тендер

Наши специалисты свяжутся с вами в ближайшее время!"""
        return ChatResponse(response=fallback, session_id=session_id)

# ==================== URL PARSER ENDPOINT ====================

@api_router.post("/parse-url", response_model=ParsedCarData)
async def parse_car_url(request: ParseUrlRequest):
    """Parse car listing URL from Chinese platforms and extract car data using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    url = request.url.strip()
    
    # Validate URL
    supported_domains = ['che168.com', '58.com', 'guazi.com', 'dongchedi.com', 'autohome.com.cn', 'taoche.com']
    is_supported = any(domain in url for domain in supported_domains)
    
    if not is_supported:
        return ParsedCarData(
            success=False,
            source_url=url,
            error="Неподдерживаемая площадка. Поддерживаются: che168.com, 58.com, guazi.com, dongchedi.com"
        )
    
    try:
        # Fetch the page content
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=req_headers)
            
            if response.status_code != 200:
                return ParsedCarData(
                    success=False,
                    source_url=url,
                    error=f"Не удалось загрузить страницу (код {response.status_code}). Попробуйте ввести данные вручную."
                )
            
            html_content = response.text
            
            # Check if page has meaningful content
            if len(html_content) < 1000:
                return ParsedCarData(
                    success=False,
                    source_url=url,
                    error="Страница пуста или защищена. Введите данные вручную."
                )
            
            # Limit content size for AI processing
            if len(html_content) > 50000:
                html_content = html_content[:50000]
        
        # Use AI to extract car data from HTML
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return ParsedCarData(
                success=False,
                source_url=url,
                error="AI сервис не настроен"
            )
        
        extraction_prompt = f"""Извлеки информацию об автомобиле из HTML-страницы китайской площадки.

URL: {url}

HTML содержимое (фрагмент):
{html_content[:25000]}

ВАЖНО: Ищи в HTML следующие данные:
- Название/title страницы часто содержит марку и модель
- Цена может быть в формате "XX.XX万" (万 = 10000 юаней) или просто числом
- Год выпуска обычно 4 цифры (2020-2025)
- Пробег может быть в 万公里 (万 = 10000 км)

Верни данные в формате JSON:
{{
    "brand": "марка авто (BYD, Li Auto, Geely, Chery, Haval, NIO, Changan, Hongqi, Zeekr, Xpeng, Volkswagen, Toyota и др.)",
    "model": "модель авто",
    "year": число (год выпуска, 2015-2025),
    "price_cny": число (цена в юанях. ВАЖНО: если цена в 万, умножь на 10000. Например 15.8万 = 158000),
    "engine_type": "ice" или "hybrid" или "electric" (определи по названию модели или характеристикам),
    "engine_volume": число (объем в см³) или null,
    "mileage": число (пробег в км. ВАЖНО: если в 万公里, умножь на 10000) или null,
    "image_url": "URL фото авто" или null,
    "description": "краткое описание на русском (цвет, комплектация, состояние)"
}}

Верни ТОЛЬКО валидный JSON без пояснений."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"parse_{uuid.uuid4()}",
            system_message="Ты эксперт по извлечению данных из HTML страниц китайских автомобильных площадок. Отвечай только валидным JSON."
        ).with_model("openai", "gpt-4o")
        
        ai_response = await chat.send_message(UserMessage(text=extraction_prompt))
        
        # Parse AI response
        import json
        import re
        
        # Try to extract JSON from response - handle nested braces
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL)
        if not json_match:
            # Try simpler pattern
            json_match = re.search(r'\{.*?\}', ai_response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                
                # Check if we got at least brand or model
                if not data.get('brand') and not data.get('model'):
                    return ParsedCarData(
                        success=False,
                        source_url=url,
                        error="Не удалось определить марку/модель авто. Страница может быть защищена. Введите данные вручную."
                    )
                
                # Validate and convert data
                engine_type = data.get('engine_type', 'ice')
                if engine_type not in ['ice', 'hybrid', 'electric']:
                    engine_type = 'ice'
                
                # Safe number conversion
                def safe_int(val):
                    if val is None:
                        return None
                    try:
                        return int(float(val))
                    except:
                        return None
                
                def safe_float(val):
                    if val is None:
                        return None
                    try:
                        return float(val)
                    except:
                        return None
                
                return ParsedCarData(
                    success=True,
                    brand=data.get('brand'),
                    model=data.get('model'),
                    year=safe_int(data.get('year')),
                    price_cny=safe_float(data.get('price_cny')),
                    engine_type=engine_type,
                    engine_volume=safe_int(data.get('engine_volume')),
                    mileage=safe_int(data.get('mileage')),
                    image_url=data.get('image_url'),
                    description=data.get('description'),
                    source_url=url
                )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error(f"Failed to parse AI response: {e}, response: {ai_response[:500]}")
        
        return ParsedCarData(
            success=False,
            source_url=url,
            error="Не удалось извлечь данные. Страница может быть защищена от парсинга. Введите данные вручную."
        )
        
    except httpx.TimeoutException:
        return ParsedCarData(
            success=False,
            source_url=url,
            error="Превышено время ожидания. Китайский сайт не отвечает."
        )
    except Exception as e:
        logger.error(f"URL parsing error: {e}")
        return ParsedCarData(
            success=False,
            source_url=url,
            error=f"Ошибка при обработке ссылки: {str(e)}"
        )

# ==================== CATALOG ENDPOINTS ====================

def generate_search_links(brand: str = None, model: str = None, query: str = None):
    """Generate search URLs for Chinese car platforms"""
    import urllib.parse
    
    search_term = query or f"{brand or ''} {model or ''}".strip()
    search_cn = search_term  # Could add translation here
    encoded = urllib.parse.quote(search_term)
    encoded_cn = urllib.parse.quote(search_cn)
    
    return {
        "che168": f"https://www.che168.com/china/a0_0msdgscncgpi1ltocsp1exx0/?keyword={encoded}",
        "58": f"https://m.58.com/ershouche/?keyword={encoded}",
        "guazi": f"https://www.guazi.com/buy/?search={encoded}",
        "dongchedi": f"https://www.dongchedi.com/search?keyword={encoded}",
    }

@api_router.get("/catalog/brands")
async def get_catalog_brands():
    """Get list of all brands in catalog - fetches live data from Che168 API"""
    try:
        # Try to get live data from Che168 API (primary source)
        che168_brands = await Che168API.get_brands()
        if che168_brands:
            return che168_brands
    except Exception as e:
        logger.error(f"Error fetching Che168 brands: {e}")
    
    try:
        # Fallback to pro-auctions
        live_brands = await ProAuctionsParser.get_brands()
        if live_brands:
            return live_brands
    except Exception as e:
        logger.error(f"Error fetching pro-auctions brands: {e}")
    
    # Fallback to static data
    brands = {}
    for car in CHINESE_CAR_CATALOG:
        if car["brand"] not in brands:
            brands[car["brand"]] = {
                "name": car["brand"],
                "name_cn": car["brand_cn"],
                "count": 0,
                "models": []
            }
        brands[car["brand"]]["count"] += 1
        if car["model"] not in brands[car["brand"]]["models"]:
            brands[car["brand"]]["models"].append(car["model"])
    
    return list(brands.values())

@api_router.get("/catalog/models/{brand_slug}")
async def get_catalog_models(brand_slug: str):
    """Get list of all models for a specific brand"""
    try:
        # Try Che168 API first
        models = await Che168API.get_models(brand_slug)
        if models:
            return models
    except Exception as e:
        logger.error(f"Error fetching models from Che168 for {brand_slug}: {e}")
    
    try:
        # Fallback to pro-auctions
        models = await ProAuctionsParser.get_models(brand_slug)
        if models:
            return models
    except Exception as e:
        logger.error(f"Error fetching models from pro-auctions for {brand_slug}: {e}")
    
    return []

@api_router.get("/catalog/search", response_model=CatalogSearchResult)
async def search_catalog(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    engine_type: Optional[str] = None,
    body_type: Optional[str] = None,
    query: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Search cars in catalog with filters - fetches live data from Che168 API"""
    
    # Try Che168 API first (primary source with real listings)
    try:
        che168_result = await Che168API.search_cars(
            mark=brand,
            model=model,
            year_from=min_year,
            year_to=max_year,
            price_from=min_price,
            price_to=max_price,
            engine_type=engine_type,
            body_type=body_type,
            page=page,
            per_page=limit
        )
        
        if che168_result["cars"]:
            # Apply query filter if present
            cars = che168_result["cars"]
            if query:
                query_lower = query.lower()
                cars = [c for c in cars if 
                    query_lower in c["brand"].lower() or 
                    query_lower in c["model"].lower() or
                    query_lower in c.get("description", "").lower()
                ]
            
            # Generate search links
            search_links = generate_search_links(brand, model, query)
            
            # Convert to response model
            cars_for_response = []
            for c in cars:
                car_dict = {
                    "id": c["id"],
                    "brand": c["brand"],
                    "brand_cn": c.get("brand_cn", ""),
                    "model": c["model"],
                    "model_cn": c.get("model_cn", ""),
                    "year_from": c["year_from"],
                    "year_to": c.get("year_to"),
                    "price_from_cny": c["price_from_cny"],
                    "price_to_cny": c.get("price_to_cny", c["price_from_cny"]),
                    "engine_type": c["engine_type"],
                    "engine_volume": c.get("engine_volume"),
                    "body_type": c["body_type"],
                    "image_url": c["image_url"],
                    "description": c.get("description", ""),
                    "features": c.get("features", []),
                    "popularity": c.get("popularity", 80),
                    "mileage": c.get("mileage"),
                    "source": "che168",
                    "fuel_type": c.get("fuel_type", "Бензин"),
                    "source_url": c.get("source_url", ""),
                    "transmission": c.get("transmission", ""),
                    "color": c.get("color", ""),
                    "address": c.get("address", ""),
                    "vin": c.get("vin", ""),
                    "power": c.get("power", 0)
                }
                cars_for_response.append(CatalogCarModel(**car_dict))
            
            return CatalogSearchResult(
                cars=cars_for_response,
                total=che168_result["total"],
                page=page,
                pages=che168_result["pages"],
                search_links=search_links
            )
    except Exception as e:
        logger.error(f"Error fetching from Che168 API: {e}")
    
    # Fallback to pro-auctions
    try:
        # Try to get live data from pro-auctions
        # Find brand slug if brand name provided
        brand_slug = None
        model_slug = None
        
        if brand:
            live_brands = await ProAuctionsParser.get_brands()
            for b in live_brands:
                if b["name"].lower() == brand.lower():
                    brand_slug = b["slug"]
                    break
        
        # Find model slug if model name provided
        if brand_slug and model:
            live_models = await ProAuctionsParser.get_models(brand_slug)
            for m in live_models:
                if m["name"].lower() == model.lower() or model.lower() in m["name"].lower():
                    model_slug = m["slug"]
                    break
        
        live_result = await ProAuctionsParser.search_cars(brand=brand_slug, model=model_slug, page=page, limit=limit)
        
        if live_result["cars"]:
            # Apply additional filters to live data
            filtered = live_result["cars"]
            
            # Only filter by model if we didn't find a model_slug (fuzzy match)
            if model and not model_slug:
                filtered = [c for c in filtered if model.lower() in c["model"].lower()]
            
            if min_price:
                filtered = [c for c in filtered if c["price_from_cny"] >= min_price]
            
            if max_price:
                filtered = [c for c in filtered if c["price_from_cny"] <= max_price]
            
            if min_year:
                filtered = [c for c in filtered if c["year_to"] is None or c["year_to"] >= min_year]
            
            if max_year:
                filtered = [c for c in filtered if c["year_from"] <= max_year]
            
            if engine_type:
                filtered = [c for c in filtered if c["engine_type"] == engine_type]
            
            if body_type:
                filtered = [c for c in filtered if c["body_type"] == body_type]
            
            if query:
                query_lower = query.lower()
                filtered = [c for c in filtered if 
                    query_lower in c["brand"].lower() or 
                    query_lower in c["model"].lower() or
                    query_lower in c.get("description", "").lower()
                ]
            
            # Generate search links
            search_links = generate_search_links(brand, model, query)
            
            # Create CatalogCarModel compatible objects
            cars_for_response = []
            for c in filtered:
                car_dict = {
                    "id": c["id"],
                    "brand": c["brand"],
                    "brand_cn": c.get("brand_cn", ""),
                    "model": c["model"],
                    "model_cn": c.get("model_cn", ""),
                    "year_from": c["year_from"],
                    "year_to": c.get("year_to"),
                    "price_from_cny": c["price_from_cny"],
                    "price_to_cny": c.get("price_to_cny", c["price_from_cny"]),
                    "engine_type": c["engine_type"],
                    "engine_volume": c.get("engine_volume"),
                    "body_type": c["body_type"],
                    "image_url": c["image_url"],
                    "description": c.get("description", ""),
                    "features": c.get("features", []),
                    "popularity": c.get("popularity", 50),
                    "mileage": c.get("mileage"),
                    "source": c.get("source", "pro-auctions"),
                    "fuel_type": c.get("fuel_type", "Бензин")
                }
                cars_for_response.append(CatalogCarModel(**car_dict))
            
            total = live_result["total"] if not any([model, min_price, max_price, min_year, max_year, engine_type, body_type, query]) else len(filtered)
            
            return CatalogSearchResult(
                cars=cars_for_response,
                total=total,
                page=page,
                pages=live_result["pages"],
                search_links=search_links
            )
    except Exception as e:
        logger.error(f"Error fetching live catalog: {e}")
    
    # Fallback to static data
    filtered = CHINESE_CAR_CATALOG.copy()
    
    # Apply filters
    if brand:
        filtered = [c for c in filtered if c["brand"].lower() == brand.lower()]
    
    if model:
        filtered = [c for c in filtered if model.lower() in c["model"].lower()]
    
    if min_price:
        filtered = [c for c in filtered if c["price_from_cny"] >= min_price]
    
    if max_price:
        filtered = [c for c in filtered if c["price_from_cny"] <= max_price]
    
    if min_year:
        filtered = [c for c in filtered if c["year_to"] is None or c["year_to"] >= min_year]
    
    if max_year:
        filtered = [c for c in filtered if c["year_from"] <= max_year]
    
    if engine_type:
        filtered = [c for c in filtered if c["engine_type"] == engine_type]
    
    if body_type:
        filtered = [c for c in filtered if c["body_type"] == body_type]
    
    if query:
        query_lower = query.lower()
        filtered = [c for c in filtered if 
            query_lower in c["brand"].lower() or 
            query_lower in c["model"].lower() or
            query_lower in c["description"].lower() or
            query_lower in c["brand_cn"] or
            query_lower in c["model_cn"]
        ]
    
    # Sort by popularity
    filtered.sort(key=lambda x: x["popularity"], reverse=True)
    
    # Pagination
    total = len(filtered)
    pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated = filtered[start:end]
    
    # Generate search links
    search_links = generate_search_links(brand, model, query)
    
    return CatalogSearchResult(
        cars=[CatalogCarModel(**c) for c in paginated],
        total=total,
        page=page,
        pages=pages,
        search_links=search_links
    )

@api_router.get("/catalog/{car_id}")
async def get_catalog_car(car_id: str):
    """Get single car details from catalog"""
    # First check static catalog
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            return {
                **car,
                "search_links": generate_search_links(car["brand"], car["model"])
            }
    
    # If not found, it might be a live car from pro-auctions
    # The car_id format from pro-auctions is like "2_10412458"
    return {
        "id": car_id,
        "brand": "Unknown",
        "model": "Unknown",
        "message": "Car details not available",
        "search_links": {}
    }

@api_router.post("/catalog/{car_id}/add-to-garage")
async def add_catalog_car_to_garage(
    car_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Add car from catalog to user's garage"""
    catalog_car = None
    
    # First check static catalog
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            catalog_car = car
            break
    
    # If not in static catalog, check Che168 cache
    if not catalog_car:
        for key in list(_cache.keys()):
            if key.startswith("che168_search_"):
                cached_data = _cache.get(key, {})
                cars = cached_data.get("cars", [])
                for car in cars:
                    if car["id"] == car_id:
                        catalog_car = car
                        break
                if catalog_car:
                    break
    
    # If still not found, check pro-auctions cache (fallback)
    if not catalog_car:
        for key in list(_cache.keys()):
            if key.startswith("pro_auctions_cars_"):
                cached_data = _cache.get(key, {})
                cars = cached_data.get("cars", [])
                for car in cars:
                    if car["id"] == car_id:
                        catalog_car = car
                        break
                if catalog_car:
                    break
    
    # If still not found and it's a Che168 ID, fetch from API
    if not catalog_car and car_id.startswith("che168-"):
        inner_id = car_id.replace("che168-", "")
        try:
            car_details = await Che168API.get_offer_details(inner_id)
            if car_details:
                catalog_car = {
                    "id": car_id,
                    "brand": car_details.get("mark", "Unknown"),
                    "model": car_details.get("model", "Unknown"),
                    "year_from": car_details.get("year", 2023),
                    "year_to": car_details.get("year", 2023),
                    "price_from_cny": car_details.get("price", 0),
                    "engine_type": Che168API.map_engine_type(car_details.get("engine_type", "")),
                    "engine_volume": int(float(car_details.get("displacement", 0) or 0) * 1000) or None,
                    "mileage": car_details.get("km_age"),
                    "image_url": car_details.get("images", [""])[0] if car_details.get("images") else "",
                    "source_url": car_details.get("url", ""),
                    "description": car_details.get("description", ""),
                    "body_type": Che168API.map_body_type(car_details.get("body_type", ""))
                }
        except Exception as e:
            logger.error(f"Error fetching car details from Che168: {e}")
    
    if not catalog_car:
        raise HTTPException(status_code=404, detail="Car not found in catalog")
    
    # Calculate Belarus price
    price_cny = catalog_car.get("price_from_cny", 0)
    engine_type = catalog_car.get("engine_type", "ice")
    engine_volume = catalog_car.get("engine_volume") or 2000
    car_year = catalog_car.get("year_to") or catalog_car.get("year_from", 2023)
    
    calculated_price_usd = None
    calculated_price_byn = None
    
    if price_cny > 0:
        try:
            # Calculate age
            current_year = datetime.now().year
            car_age = current_year - car_year
            age = "under3" if car_age < 3 else ("3to5" if car_age < 5 else "over5")
            
            # Use calculator logic
            calc_input = CalculatorInput(
                price_cny=price_cny,
                age=age,
                engine_type=engine_type,
                engine_volume=engine_volume,
                user_type="individual",
                use_decree_140=False,
                payment_via_platform=True
            )
            calc_result = await calculate_customs(calc_input)
            calculated_price_usd = calc_result.total_usd
            calculated_price_byn = calc_result.total_byn
        except Exception as e:
            print(f"Price calculation error: {e}")
    
    # Create garage entry
    garage_id = str(uuid.uuid4())
    garage_doc = {
        "id": garage_id,
        "user_id": current_user["id"],
        "brand": catalog_car["brand"],
        "model": catalog_car["model"],
        "year": car_year,
        "price_cny": price_cny,
        "engine_type": engine_type,
        "engine_volume": catalog_car.get("engine_volume"),
        "mileage": catalog_car.get("mileage"),
        "image_url": catalog_car.get("image_url"),
        "source_url": catalog_car.get("source_url"),
        "description": catalog_car.get("description", ""),
        "calculated_price_usd": calculated_price_usd,
        "calculated_price_byn": calculated_price_byn,
        "status": "saved",
        "from_catalog": True,
        "catalog_id": car_id,
        "source": catalog_car.get("source", "static"),
        "price_rub": catalog_car.get("price_rub"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.garage.insert_one(garage_doc)
    
    return {"message": "Car added to garage", "garage_id": garage_id, "calculated_price_usd": calculated_price_usd}

# ==================== CLIENT VERIFICATION SYSTEM ====================

class ClientVerificationCreate(BaseModel):
    full_name: str
    passport_series: str
    passport_number: str
    passport_issued_by: str
    passport_issue_date: str
    registration_address: str
    phone: str
    email: EmailStr
    client_type: Literal["individual", "legal"] = "individual"
    # For legal entities
    company_name: Optional[str] = None
    company_unp: Optional[str] = None
    company_address: Optional[str] = None

@api_router.post("/verification/submit")
async def submit_verification(data: ClientVerificationCreate, current_user: dict = Depends(get_current_user)):
    """Submit client verification data"""
    verification_id = str(uuid.uuid4())
    
    # Generate contract number
    contract_number = f"CB-{datetime.now().strftime('%Y%m%d')}-{verification_id[:8].upper()}"
    
    verification_doc = {
        "id": verification_id,
        "user_id": current_user["id"],
        "contract_number": contract_number,
        "full_name": data.full_name,
        "passport_series": data.passport_series,
        "passport_number": data.passport_number,
        "passport_issued_by": data.passport_issued_by,
        "passport_issue_date": data.passport_issue_date,
        "registration_address": data.registration_address,
        "phone": data.phone,
        "email": data.email,
        "client_type": data.client_type,
        "company_name": data.company_name,
        "company_unp": data.company_unp,
        "company_address": data.company_address,
        "documents": [],
        "status": "pending",  # pending, documents_uploaded, under_review, approved, rejected
        "contract_generated": False,
        "contract_signed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.verifications.insert_one(verification_doc)
    
    # Update user account with verification status
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {
            "$set": {
                "verification_id": verification_id,
                "verification_status": "pending",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {
        "message": "Данные верификации отправлены",
        "verification_id": verification_id,
        "contract_number": contract_number
    }

@api_router.get("/verification/status")
async def get_verification_status(current_user: dict = Depends(get_current_user)):
    """Get current user's verification status"""
    verification = await db.verifications.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not verification:
        return {"status": "not_started", "verification": None}
    
    return {"status": verification.get("status"), "verification": verification}

@api_router.post("/verification/upload-document")
async def upload_verification_document(data: dict, current_user: dict = Depends(get_current_user)):
    """Upload document for verification"""
    doc_type = data.get("doc_type")  # passport_scan, passport_back, other
    file_url = data.get("file_url")
    file_name = data.get("file_name", "document")
    
    if not doc_type or not file_url:
        raise HTTPException(status_code=400, detail="Укажите тип документа и URL файла")
    
    verification = await db.verifications.find_one({"user_id": current_user["id"]})
    if not verification:
        raise HTTPException(status_code=404, detail="Сначала заполните данные верификации")
    
    doc_id = str(uuid.uuid4())
    document = {
        "id": doc_id,
        "type": doc_type,
        "name": file_name,
        "url": file_url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "verified": False
    }
    
    await db.verifications.update_one(
        {"user_id": current_user["id"]},
        {
            "$push": {"documents": document},
            "$set": {
                "status": "documents_uploaded",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Документ загружен", "document_id": doc_id}

@api_router.get("/verification/contract")
async def get_contract(current_user: dict = Depends(get_current_user)):
    """Generate and return contract data for display/download"""
    verification = await db.verifications.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    # Contract template data
    contract_data = {
        "contract_number": verification.get("contract_number"),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "city": "Минск",
        # Executor (CARBRIDGE)
        "executor": {
            "name": "ООО «КАРБРИДЖ»",
            "director": "Вотинцев Кирилл Михайлович",
            "address": "220088, г. Минск, ул. Червякова д.52, пом. 2",
            "unp": "193973008"
        },
        # Client data
        "client": {
            "full_name": verification.get("full_name"),
            "passport_series": verification.get("passport_series"),
            "passport_number": verification.get("passport_number"),
            "passport_issued_by": verification.get("passport_issued_by"),
            "passport_issue_date": verification.get("passport_issue_date"),
            "registration_address": verification.get("registration_address"),
            "phone": verification.get("phone"),
            "email": verification.get("email"),
            "client_type": verification.get("client_type"),
            "company_name": verification.get("company_name"),
            "company_unp": verification.get("company_unp")
        },
        # Contract terms
        "terms": {
            "prepayment_byn": "1500",
            "platform_commission": "3%",
            "payment_commission": "1.5%"
        },
        "status": verification.get("status"),
        "signed": verification.get("contract_signed", False)
    }
    
    # Mark contract as generated
    if not verification.get("contract_generated"):
        await db.verifications.update_one(
            {"user_id": current_user["id"]},
            {"$set": {"contract_generated": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return contract_data

@api_router.get("/verification/contract/download")
async def download_contract_pdf(current_user: dict = Depends(get_current_user)):
    """Generate and download contract as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    verification = await db.verifications.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Get client data
    contract_number = verification.get("contract_number", "______")
    full_name = verification.get("full_name", "_____________")
    passport = f"{verification.get('passport_series', '__')} {verification.get('passport_number', '______')}"
    passport_issued = verification.get("passport_issued_by", "________________")
    passport_date = verification.get("passport_issue_date", "__________")
    address = verification.get("registration_address", "____________________")
    phone = verification.get("phone", "______________")
    email = verification.get("email", "______________")
    current_date = datetime.now().strftime("%d %B %Y")
    
    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(f"ДОГОВОР № {contract_number}", title_style))
    story.append(Paragraph("на оказание услуг по организации приобретения и доставки автомобиля", subtitle_style))
    story.append(Spacer(1, 6))
    
    # Header
    story.append(Paragraph(f'г. Минск «{datetime.now().strftime("%d")}» {datetime.now().strftime("%B")} {datetime.now().strftime("%Y")} г.', normal_style))
    story.append(Spacer(1, 6))
    
    # Parties
    intro_text = f'''Общество с ограниченной ответственностью «КАРБРИДЖ», именуемое в дальнейшем «Исполнитель», 
    в лице директора Вотинцева Кирилла Михайловича, действующего на основании Устава, с одной стороны,
    <br/><br/>и<br/><br/>
    Гражданин(ка) <b>{full_name}</b>, паспорт: серия № <b>{passport}</b>, 
    выдан <b>{passport_issued}</b> <b>{passport_date}</b>, 
    проживающий(ая) по адресу: <b>{address}</b>, 
    именуемый(ая) в дальнейшем «Заказчик», с другой стороны,
    <br/><br/>
    вместе именуемые «Стороны», заключили настоящий Договор о нижеследующем:'''
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 10))
    
    # Section 1 - Subject
    story.append(Paragraph("1. ПРЕДМЕТ ДОГОВОРА", section_style))
    story.append(Paragraph('''1.1. Исполнитель обязуется оказать Заказчику услуги по организации приобретения и доставки 
    транспортного средства (далее – «Автомобиль») из Китайской Народной Республики через цифровую платформу 
    CarBridge, а Заказчик обязуется принять и оплатить оказанные услуги в порядке и на условиях, 
    предусмотренных настоящим Договором.''', normal_style))
    
    story.append(Paragraph("1.2. В комплекс услуг Исполнителя входит:", normal_style))
    services = [
        "1.2.1. Предоставление доступа к функционалу платформы CarBridge, включая AI-агента для подбора автомобиля;",
        "1.2.2. Доступ к тендерной системе для получения предложений от китайских поставщиков;",
        "1.2.3. Координация процесса проверки технического состояния автомобиля;",
        "1.2.4. Взаимодействие с проверенными подрядчиками (продавцами) в КНР;",
        "1.2.5. Организация логистики (выбор перевозчика через тендерную систему);",
        "1.2.6. Предоставление доступа к системе GPS-мониторинга для отслеживания груза;",
        "1.2.7. Консультационная поддержка по вопросам таможенного оформления."
    ]
    for s in services:
        story.append(Paragraph(s, normal_style))
    
    # Section 2 - Procedure
    story.append(Paragraph("2. ПОРЯДОК ОКАЗАНИЯ УСЛУГ", section_style))
    story.append(Paragraph("2.1. Оказание услуг осуществляется поэтапно через личный кабинет Заказчика на платформе CarBridge:", normal_style))
    
    stages = [
        "2.1.1. Регистрация Заказчика на платформе и получение доступа к личному кабинету.",
        "2.1.2. Подбор автомобиля с использованием автоматизированного AI-агента или самостоятельный выбор из каталога.",
        "2.1.3. Формирование и утверждение Заказчиком типовой формы запроса на автомобиль.",
        "2.1.4. Внесение Заказчиком предоплаты для активации тендерной системы.",
        "2.1.5. Автоматическая рассылка запроса Исполнителем зарегистрированным подрядчикам (поставщикам) в Китае.",
        "2.1.6. Сбор и предоставление Заказчику коммерческих предложений от подрядчиков.",
        "2.1.7. Выбор Заказчиком конкретного предложения (автомобиля и поставщика).",
        "2.1.8. Организация детальной проверки автомобиля (видеообзор, фото, отчет о состоянии).",
        "2.1.9. Заключение договора купли-продажи между Заказчиком и выбранным Продавцом.",
        "2.1.10. Контроль процесса выкупа и перевода денежных средств Продавцу.",
        "2.1.11. Организация логистики: проведение тендера среди перевозчиков.",
        "2.1.12. GPS-мониторинг на всем пути следования автомобиля.",
        "2.1.13. Организация таможенного оформления: проведение тендера среди таможенных брокеров.",
        "2.1.14. Передача автомобиля Заказчику."
    ]
    for s in stages:
        story.append(Paragraph(s, normal_style))
    
    story.append(Paragraph('''2.2. Важное условие: Исполнитель предоставляет информационно-техническую платформу для организации сделки, 
    но не выступает Продавцом автомобиля. Договор купли-продажи автомобиля заключается напрямую между 
    Заказчиком и китайским поставщиком (подрядчиком). Исполнитель не становится собственником автомобиля 
    на каком-либо этапе сделки.''', normal_style))
    
    # Section 4 - Cost
    story.append(Paragraph("4. СТОИМОСТЬ УСЛУГ И ПОРЯДОК РАСЧЕТОВ", section_style))
    story.append(Paragraph('''4.1. Для начала работы и активации тендерной системы Заказчик вносит Предоплату в размере 
    <b>1500 (Тысяча пятьсот) белорусских рублей</b>. Данная сумма является обеспечением серьезности намерений 
    Заказчика и не подлежит возврату после запуска тендерной процедуры.''', normal_style))
    story.append(Paragraph('''4.2. Вознаграждение (комиссия) Исполнителя за пользование платформой и организацию сделки составляет 
    <b>3% (три процента)</b> от стоимости автомобиля (цены выкупа, указанной в инвойсе китайского поставщика).''', normal_style))
    story.append(Paragraph('''4.5.2. Оплата через платформу: за организацию платежей через платформу взимается комиссия в размере 
    <b>1,5% (один целый пять десятых процента)</b> от суммы каждого платежа.''', normal_style))
    
    # Section 7 - Term
    story.append(Paragraph("7. СРОК ДЕЙСТВИЯ И ПОРЯДОК РАСТОРЖЕНИЯ", section_style))
    story.append(Paragraph('''7.1. Настоящий Договор вступает в силу с момента совершения Заказчиком действий по регистрации 
    на платформе CarBridge и внесения предоплаты, что означает присоединение Заказчика к Договору 
    и его полное согласие со всеми условиями Договора.''', normal_style))
    story.append(Paragraph("7.2. Договор действует до полного исполнения Сторонами своих обязательств.", normal_style))
    
    # Section 10 - Signatures
    story.append(Spacer(1, 20))
    story.append(Paragraph("10. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН", section_style))
    story.append(Spacer(1, 10))
    
    # Two column table for signatures
    sig_data = [
        [Paragraph("<b>ИСПОЛНИТЕЛЬ</b>", normal_style), Paragraph("<b>ЗАКАЗЧИК</b>", normal_style)],
        [Paragraph("ООО «КАРБРИДЖ»", normal_style), Paragraph(f"Ф.И.О.: {full_name}", normal_style)],
        [Paragraph("220088, г. Минск,<br/>ул. Червякова д.52, пом. 2", normal_style), 
         Paragraph(f"Паспорт: {passport}", normal_style)],
        [Paragraph("УНП: 193973008", normal_style), Paragraph(f"Адрес: {address}", normal_style)],
        [Paragraph("", normal_style), Paragraph(f"Телефон: {phone}", normal_style)],
        [Paragraph("", normal_style), Paragraph(f"Email: {email}", normal_style)],
        [Paragraph("Директор _______________ / К.М. Вотинцев /", normal_style), 
         Paragraph("Заказчик _______________ / _____________ /", normal_style)],
        [Paragraph("М.П.", normal_style), Paragraph("", normal_style)]
    ]
    
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    
    # Update that contract was downloaded
    await db.verifications.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"contract_downloaded": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    filename = f"Dogovor_CarBridge_{contract_number}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@api_router.post("/verification/sign-contract")
async def sign_contract(current_user: dict = Depends(get_current_user)):
    """Client signs the contract"""
    verification = await db.verifications.find_one({"user_id": current_user["id"]})
    
    if not verification:
        raise HTTPException(status_code=404, detail="Верификация не найдена")
    
    if verification.get("status") not in ["documents_uploaded", "under_review", "approved"]:
        raise HTTPException(status_code=400, detail="Сначала загрузите документы")
    
    await db.verifications.update_one(
        {"user_id": current_user["id"]},
        {
            "$set": {
                "contract_signed": True,
                "contract_signed_at": datetime.now(timezone.utc).isoformat(),
                "status": "under_review",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update account
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {
            "$set": {
                "contract_signed": True,
                "verification_status": "under_review"
            }
        }
    )
    
    return {"message": "Договор подписан. Ожидайте проверки модератором."}

# ==================== CAR APPLICATION SYSTEM ====================

class CarApplicationCreate(BaseModel):
    """
    New comprehensive application form matching the PDF template.
    Структура соответствует форме заявки CarBridge.
    """
    # РАЗДЕЛ 1: Данные клиента
    client_type: Literal["individual", "legal"] = "individual"
    full_name: str
    delivery_city: Optional[str] = None
    
    # РАЗДЕЛ 2.1: Основные характеристики
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    body_type: Optional[str] = None  # sedan, hatchback, coupe, minivan, wagon, pickup, suv, any
    
    # РАЗДЕЛ 2.2: Двигатель и трансмиссия
    engine_type: Optional[str] = None  # petrol, diesel, electric, hybrid, phev, gas
    engine_volume: Optional[str] = None  # lt1, 1_15, 15_2, 2_25, 25_3, gt3, any
    power_from: Optional[int] = None
    power_to: Optional[int] = None
    transmission: Optional[str] = None  # mt, at, amt_dsg, cvt, reducer, any
    drive_type: Optional[str] = None  # fwd, rwd, awd, any
    
    # РАЗДЕЛ 2.3: Внешний вид
    body_color: Optional[str] = None  # white, black, grey, silver, blue, red, brown, green, other, any
    body_color_other: Optional[str] = None  # если выбрано "other"
    exact_color: Optional[str] = None  # точный цвет
    color_importance: Optional[str] = None  # required, preferred, not_important
    interior_color: Optional[str] = None  # black, beige, grey, brown, combi, other, any
    interior_color_other: Optional[str] = None
    interior_material: Optional[str] = None  # leather, eco_leather, fabric, alcantara, any
    
    # РАЗДЕЛ 3.1: Пробег
    mileage_max: Optional[str] = None  # lt10, lt30, lt50, lt80, lt100, gt100, any
    car_condition: Optional[str] = None  # new, used, any
    
    # РАЗДЕЛ 3.2: Допустимые повреждения
    allow_damage: bool = False
    damage_level: Optional[str] = None  # level1, level12, level123, new_only
    damage_comment: Optional[str] = None
    
    # РАЗДЕЛ 4: Дополнительные опции
    # Электронные системы
    options_electronic: Optional[List[str]] = None  # system_360, acc, lka, autopark, parking_sensors, rear_camera, wireless_charge, hud, carplay
    # Комфорт
    options_comfort: Optional[List[str]] = None  # panoramic_roof, heated_front, heated_rear, ventilated_seats, massage_seats, seat_memory, climate_control, heated_wheel, electric_trunk, keyless
    # Внешний вид
    options_exterior: Optional[List[str]] = None  # sport_package, wheels_r18, led_matrix, factory_tint
    # Прочее
    options_other: Optional[List[str]] = None  # towbar, spare_wheel, third_row, premium_audio
    required_options: Optional[str] = None
    preferred_options: Optional[str] = None
    
    # РАЗДЕЛ 5: Бюджет и условия
    budget_china_from: Optional[float] = None  # бюджет в Китае (USD) от
    budget_china_to: Optional[float] = None  # бюджет в Китае (USD) до
    budget_total: Optional[float] = None  # общий бюджет до (с доставкой и таможней)
    purchase_timeline: Optional[str] = None  # urgent, 1month, 2_3months, not_rush
    payment_method: Optional[str] = None  # full_prepay, installment, credit_leasing
    car_purpose: Optional[str] = None  # personal, business, taxi, resale
    customs_clearance: Optional[str] = None  # carbridge, self, unknown
    
    # РАЗДЕЛ 6: Приоритеты и комментарии
    priority_price: Optional[int] = None  # 1-5
    priority_reliability: Optional[int] = None  # 1-5
    priority_technology: Optional[int] = None  # 1-5
    priority_prestige: Optional[int] = None  # 1-5
    priority_fuel: Optional[int] = None  # 1-5
    additional_requirements: Optional[str] = None
    
    # Legacy fields for backward compatibility (kept but deprecated)
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_contact: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: Optional[str] = None
    color_preferences: Optional[str] = None
    has_decree_140: bool = False
    decree_140_category: Optional[str] = None
    needs_manager_help: bool = False
    urgent: bool = False

@api_router.post("/applications/create")
async def create_car_application(data: CarApplicationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new car application - new comprehensive form matching PDF template"""
    application_id = str(uuid.uuid4())
    application_number = f"APP-{datetime.now().strftime('%Y%m%d')}-{application_id[:6].upper()}"
    
    application_doc = {
        "id": application_id,
        "application_number": application_number,
        "user_id": current_user["id"],
        
        # РАЗДЕЛ 1: Данные клиента
        "client_type": data.client_type,
        "full_name": data.full_name,
        "delivery_city": data.delivery_city,
        
        # РАЗДЕЛ 2.1: Основные характеристики
        "brand": data.brand,
        "model": data.model,
        "year_from": data.year_from,
        "year_to": data.year_to,
        "body_type": data.body_type,
        
        # РАЗДЕЛ 2.2: Двигатель и трансмиссия
        "engine_type": data.engine_type,
        "engine_volume": data.engine_volume,
        "power_from": data.power_from,
        "power_to": data.power_to,
        "transmission": data.transmission,
        "drive_type": data.drive_type,
        
        # РАЗДЕЛ 2.3: Внешний вид
        "body_color": data.body_color,
        "body_color_other": data.body_color_other,
        "exact_color": data.exact_color,
        "color_importance": data.color_importance,
        "interior_color": data.interior_color,
        "interior_color_other": data.interior_color_other,
        "interior_material": data.interior_material,
        
        # РАЗДЕЛ 3: Пробег и состояние
        "mileage_max": data.mileage_max,
        "car_condition": data.car_condition,
        "allow_damage": data.allow_damage,
        "damage_level": data.damage_level,
        "damage_comment": data.damage_comment,
        
        # РАЗДЕЛ 4: Дополнительные опции
        "options_electronic": data.options_electronic or [],
        "options_comfort": data.options_comfort or [],
        "options_exterior": data.options_exterior or [],
        "options_other": data.options_other or [],
        "required_options": data.required_options,
        "preferred_options": data.preferred_options,
        
        # РАЗДЕЛ 5: Бюджет и условия
        "budget_china_from": data.budget_china_from,
        "budget_china_to": data.budget_china_to,
        "budget_total": data.budget_total,
        "purchase_timeline": data.purchase_timeline,
        "payment_method": data.payment_method,
        "car_purpose": data.car_purpose,
        "customs_clearance": data.customs_clearance,
        
        # РАЗДЕЛ 6: Приоритеты и комментарии
        "priority_price": data.priority_price,
        "priority_reliability": data.priority_reliability,
        "priority_technology": data.priority_technology,
        "priority_prestige": data.priority_prestige,
        "priority_fuel": data.priority_fuel,
        "additional_requirements": data.additional_requirements,
        
        # Legacy fields (for backward compatibility)
        "phone": data.phone or current_user.get("phone"),
        "email": data.email or current_user.get("email"),
        "preferred_contact": data.preferred_contact,
        "budget_min": data.budget_min,
        "budget_max": data.budget_max,
        "budget_currency": data.budget_currency or "USD",
        "color_preferences": data.color_preferences,
        "has_decree_140": data.has_decree_140,
        "decree_140_category": data.decree_140_category,
        "needs_manager_help": data.needs_manager_help,
        "urgent": data.urgent,
        
        # Status
        "status": "new",
        "offers_count": 0,
        "manager_assigned": False,
        "tender_started": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.applications.insert_one(application_doc)
    
    return {
        "message": "Заявка успешно создана",
        "application_id": application_id,
        "application_number": application_number
    }

@api_router.get("/applications/my")
async def get_my_applications(current_user: dict = Depends(get_current_user)):
    """Get all applications for current user"""
    applications = await db.applications.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return applications

@api_router.get("/applications/{application_id}")
async def get_application(application_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific application"""
    application = await db.applications.find_one(
        {"id": application_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    return application

@api_router.delete("/applications/{application_id}")
async def cancel_application(application_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel application"""
    result = await db.applications.update_one(
        {"id": application_id, "user_id": current_user["id"], "status": "new"},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Невозможно отменить заявку")
    
    return {"message": "Заявка отменена"}

@api_router.post("/applications/{application_id}/request-manager-help")
async def request_manager_help_for_application(application_id: str, current_user: dict = Depends(get_current_user)):
    """Request manager help for application ($200 fee)"""
    # Check balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < CONSULTANT_FEE:
        raise HTTPException(status_code=400, detail=f"Недостаточно средств. Требуется ${CONSULTANT_FEE}")
    
    # Check application exists
    app = await db.applications.find_one({"id": application_id, "user_id": current_user["id"]})
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if app.get("manager_assigned"):
        raise HTTPException(status_code=400, detail="Менеджер уже назначен")
    
    # Deduct fee
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -CONSULTANT_FEE}}
    )
    
    # Log transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "manager_help",
        "amount": -CONSULTANT_FEE,
        "description": f"Помощь менеджера для заявки {app.get('application_number', application_id)}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update application
    await db.applications.update_one(
        {"id": application_id},
        {"$set": {"manager_assigned": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Менеджер назначен", "fee_charged": CONSULTANT_FEE}

@api_router.post("/applications/{application_id}/start-tender")
async def start_tender_from_application(application_id: str, current_user: dict = Depends(get_current_user)):
    """Start tender from application"""
    # Check verification/contract
    verification = await db.verifications.find_one({"user_id": current_user["id"]})
    if not verification or not verification.get("contract_signed"):
        raise HTTPException(status_code=403, detail="Необходимо подписать договор")
    
    # Check application
    app = await db.applications.find_one({"id": application_id, "user_id": current_user["id"]})
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if app.get("tender_started"):
        raise HTTPException(status_code=400, detail="Тендер уже запущен")
    
    # Create tender
    tender_id = str(uuid.uuid4())
    tender = {
        "id": tender_id,
        "user_id": current_user["id"],
        "application_id": application_id,
        "type": "application",
        "status": "active",
        "car_request": {
            "brand": app.get("brand"),
            "model": app.get("model"),
            "body_type": app.get("body_type"),
            "engine_type": app.get("engine_type"),
            "year_from": app.get("year_from"),
            "year_to": app.get("year_to"),
            "budget_min": app.get("budget_min"),
            "budget_max": app.get("budget_max"),
            "budget_currency": app.get("budget_currency")
        },
        "offers": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tenders.insert_one(tender)
    
    # Update application
    await db.applications.update_one(
        {"id": application_id},
        {"$set": {
            "tender_started": True, 
            "tender_id": tender_id,
            "status": "in_progress",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Тендер запущен", "tender_id": tender_id}

@api_router.post("/deals/request-assistance")
async def request_deal_assistance(current_user: dict = Depends(get_current_user)):
    """Request consultant assistance ($200 fee)"""
    # Check balance
    account = await db.accounts.find_one({"user_id": current_user["id"]})
    balance = account.get("balance", 0) if account else 0
    
    if balance < CONSULTANT_FEE:
        raise HTTPException(status_code=400, detail=f"Недостаточно средств. Требуется ${CONSULTANT_FEE}")
    
    # Deduct fee
    await db.accounts.update_one(
        {"user_id": current_user["id"]},
        {"$inc": {"balance": -CONSULTANT_FEE}}
    )
    
    # Log transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "consultant_help",
        "amount": -CONSULTANT_FEE,
        "description": "Помощь консультанта",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Запрос на помощь консультанта отправлен", "fee_charged": CONSULTANT_FEE}

# ==================== CONTRACTOR SYSTEM ====================

class ServicePricing(BaseModel):
    """Pricing for a single service"""
    service: str  # inspection, purchase, export, logistics, leasing, customs
    price_usd: float
    description: Optional[str] = None

class ContractorRegister(BaseModel):
    # Company info
    company_name: str
    country: Literal["BY", "CN"] = "CN"  # Belarus or China
    registration_number: Optional[str] = None  # UNP for BY, USCI for CN
    legal_address: str
    
    # Login credentials
    email: EmailStr
    password: str  # Password for contractor login
    
    # Contact person
    contact_person: str
    position: str
    phone: str
    whatsapp: Optional[str] = None
    wechat: Optional[str] = None
    telegram: Optional[str] = None
    
    # Services offered with pricing
    services: List[str]  # inspection, purchase, export, logistics, leasing, customs
    service_prices: Optional[dict] = None  # {service_name: price_usd}
    
    # Additional info
    description: str
    experience_years: Optional[int] = None
    website: Optional[str] = None

@api_router.post("/contractors/register")
async def register_contractor(data: ContractorRegister):
    """Register a new contractor"""
    # Check if email already registered
    existing = await db.contractor_applications.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    contractor_id = str(uuid.uuid4())
    password_hash = pwd_context.hash(data.password)
    
    contractor_doc = {
        "id": contractor_id,
        "company_name": data.company_name,
        "country": data.country,
        "registration_number": data.registration_number,
        "legal_address": data.legal_address,
        "contact_person": data.contact_person,
        "position": data.position,
        "phone": data.phone,
        "email": data.email,
        "password_hash": password_hash,  # Store password hash
        "whatsapp": data.whatsapp,
        "wechat": data.wechat,
        "telegram": data.telegram,
        "services": data.services,
        "service_prices": data.service_prices or {},  # Store service pricing
        "description": data.description,
        "experience_years": data.experience_years,
        "website": data.website,
        "documents": [],
        "status": "pending",  # pending, under_review, approved, rejected
        "verified": False,
        "rating": 5.0,
        "deals_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contractor_applications.insert_one(contractor_doc)
    
    return {
        "message": "Заявка на регистрацию подрядчика отправлена. После одобрения вы сможете войти с указанным паролем.",
        "contractor_id": contractor_id
    }

@api_router.post("/contractors/login")
async def contractor_login(credentials: UserLogin):
    """Login for contractors"""
    contractor = await db.contractors.find_one({"email": credentials.email})
    
    if not contractor:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    if not verify_password(credentials.password, contractor.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    if contractor.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Аккаунт не активирован")
    
    # Generate token
    token_data = {
        "sub": contractor["id"],
        "email": contractor["email"],
        "type": "contractor",
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "contractor": {
            "id": contractor["id"],
            "company_name": contractor["company_name"],
            "email": contractor["email"],
            "services": contractor.get("services", []),
            "verified": contractor.get("verified", False),
            "rating": contractor.get("rating", 5.0)
        }
    }

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

@api_router.get("/contractor-dashboard")
async def get_contractor_dashboard(contractor: dict = Depends(get_current_contractor)):
    """Get contractor dashboard data"""
    # Get active tenders
    tenders = await db.tenders.find(
        {"status": "active"},
        {"_id": 0}
    ).to_list(50)
    
    # Get contractor's offers
    my_offers = await db.tender_offers.find(
        {"contractor_id": contractor["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get completed deals
    completed_deals = await db.deals.find(
        {"contractor_id": contractor["id"], "status": "completed"},
        {"_id": 0}
    ).to_list(100)
    
    # Get applications looking for contractors
    applications = await db.applications.find(
        {"status": {"$in": ["new", "in_progress"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {
        "contractor": {
            "id": contractor["id"],
            "company_name": contractor["company_name"],
            "services": contractor.get("services", []),
            "verified": contractor.get("verified", False),
            "rating": contractor.get("rating", 5.0),
            "deals_count": contractor.get("deals_count", 0)
        },
        "active_tenders": len(tenders),
        "my_offers": len(my_offers),
        "completed_deals": len(completed_deals),
        "new_applications": len([a for a in applications if a.get("status") == "new"]),
        "tenders": tenders[:10],
        "recent_offers": my_offers[:10],
        "applications": applications[:10]
    }

@api_router.post("/contractor-offers")
async def submit_contractor_offer(data: dict, contractor: dict = Depends(get_current_contractor)):
    """Submit offer for a tender or application"""
    tender_id = data.get("tender_id")
    application_id = data.get("application_id")
    
    if not tender_id and not application_id:
        raise HTTPException(status_code=400, detail="Укажите tender_id или application_id")
    
    offer_id = str(uuid.uuid4())
    
    offer_doc = {
        "id": offer_id,
        "contractor_id": contractor["id"],
        "contractor_name": contractor["company_name"],
        "tender_id": tender_id,
        "application_id": application_id,
        "price_usd": data.get("price_usd"),
        "price_cny": data.get("price_cny"),
        "delivery_days": data.get("delivery_days"),
        "delivery_cost": data.get("delivery_cost"),
        "car_details": data.get("car_details"),
        "notes": data.get("notes"),
        "valid_until": data.get("valid_until"),
        "status": "pending",  # pending, accepted, rejected
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tender_offers.insert_one(offer_doc)
    
    # Update tender/application offers count
    if tender_id:
        await db.tenders.update_one(
            {"id": tender_id},
            {"$inc": {"offers_count": 1}}
        )
    if application_id:
        await db.applications.update_one(
            {"id": application_id},
            {"$inc": {"offers_count": 1}, "$set": {"status": "offers_received"}}
        )
    
    return {"message": "Предложение отправлено", "offer_id": offer_id}

# Moderator endpoints for contractor management
@api_router.get("/moderator/contractor-applications")
async def get_contractor_applications(current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Get all contractor applications"""
    applications = await db.contractor_applications.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return applications

@api_router.post("/moderator/contractors/{contractor_id}/approve")
async def approve_contractor(contractor_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Approve contractor application"""
    application = await db.contractor_applications.find_one({"id": contractor_id})
    
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    # Use password from application (set during registration) or generate new one
    password_hash = application.get("password_hash")
    temp_password = None
    
    if not password_hash:
        # Legacy: generate temp password for old applications without password
        temp_password = str(uuid.uuid4())[:12]
        password_hash = pwd_context.hash(temp_password)
    
    # Create contractor account
    contractor_doc = {
        **{k: v for k, v in application.items() if k != "_id"},
        "password_hash": password_hash,
        "status": "approved",
        "verified": data.get("verified", True),
        "approved_by": current_user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contractors.insert_one(contractor_doc)
    
    # Update application status
    await db.contractor_applications.update_one(
        {"id": contractor_id},
        {"$set": {"status": "approved"}}
    )
    
    response = {
        "message": "Подрядчик одобрен",
        "email": application["email"]
    }
    
    if temp_password:
        response["temp_password"] = temp_password
        response["note"] = "Временный пароль (заявка без пароля)"
    else:
        response["note"] = "Подрядчик может войти с паролем, указанным при регистрации"
    
    return response

@api_router.post("/moderator/contractors/{contractor_id}/reject")
async def reject_contractor(contractor_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Reject contractor application"""
    reason = data.get("reason", "")
    
    await db.contractor_applications.update_one(
        {"id": contractor_id},
        {
            "$set": {
                "status": "rejected",
                "rejection_reason": reason,
                "rejected_by": current_user["id"],
                "rejected_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Заявка отклонена"}

# ==================== GPS TRACKING ENDPOINT ====================

@api_router.get("/deals/{deal_id}/tracking")
async def get_deal_tracking(deal_id: str, current_user: dict = Depends(get_current_user)):
    """Get GPS tracking data for a deal"""
    deal = await db.deals.find_one({"id": deal_id, "user_id": current_user["id"]})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Check if tracking data exists
    tracking = await db.tracking.find_one({"deal_id": deal_id})
    
    if tracking:
        # Return existing tracking data
        return {
            "deal_id": deal_id,
            "car_info": deal.get("car_info"),
            "current_stage": tracking.get("current_stage", "china_warehouse"),
            "current_location": tracking.get("current_location"),
            "progress": tracking.get("progress", 0),
            "estimated_arrival": tracking.get("estimated_arrival"),
            "history": tracking.get("history", []),
            "last_updated": tracking.get("last_updated")
        }
    
    # Generate tracking based on deal stages
    stages = deal.get("stages", {})
    
    # Determine current tracking stage
    tracking_stage = "china_warehouse"
    progress = 0
    
    if stages.get("customs", {}).get("completed") or stages.get("customs", {}).get("paid"):
        tracking_stage = "delivery"
        progress = 85
    elif stages.get("delivery_rb", {}).get("completed") or stages.get("delivery_rb", {}).get("paid"):
        tracking_stage = "customs"
        progress = 70
    elif stages.get("insurance", {}).get("completed") or stages.get("insurance", {}).get("skipped"):
        tracking_stage = "eu_port"
        progress = 55
    elif stages.get("logistics_china", {}).get("completed") or stages.get("logistics_china", {}).get("skipped"):
        tracking_stage = "in_transit"
        progress = 40
    elif stages.get("export", {}).get("completed") or stages.get("export", {}).get("paid"):
        tracking_stage = "china_port"
        progress = 20
    
    # Location data
    locations = {
        "china_warehouse": {"lat": 31.2304, "lng": 121.4737, "city": "Шанхай"},
        "china_port": {"lat": 22.5431, "lng": 114.0579, "city": "Шэньчжэнь"},
        "in_transit": {"lat": 35.6762, "lng": 139.6503, "city": "В море"},
        "eu_port": {"lat": 54.6872, "lng": 25.2797, "city": "Клайпеда"},
        "customs": {"lat": 53.9006, "lng": 27.5590, "city": "Минск"},
        "delivery": {"lat": 53.9006, "lng": 27.5590, "city": "Минск"}
    }
    
    # Calculate estimated arrival
    days_remaining = max(0, int((100 - progress) / 15))
    estimated_arrival = (datetime.now(timezone.utc) + timedelta(days=days_remaining)).isoformat()
    
    return {
        "deal_id": deal_id,
        "car_info": deal.get("car_info"),
        "current_stage": tracking_stage,
        "current_location": locations.get(tracking_stage),
        "progress": progress,
        "estimated_arrival": estimated_arrival,
        "history": [],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

# ==================== STATUS ENDPOINT ====================

@api_router.get("/")
async def root():
    return {"message": "CARBRIDGE API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router and configure app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
