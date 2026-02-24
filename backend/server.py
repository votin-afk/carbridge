from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

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
    status: str
    created_at: str

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
    car_id: str
    car_info: Optional[dict] = None
    status: str
    offers: List[dict] = []
    selected_offer_id: Optional[str] = None
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
    brand_cn: str
    model: str
    model_cn: str
    year_from: int
    year_to: Optional[int] = None
    price_from_cny: float
    price_to_cny: Optional[float] = None
    engine_type: str
    engine_volume: Optional[int] = None
    body_type: str
    image_url: str
    description: str
    features: List[str] = []
    popularity: int = 0

class CatalogSearchResult(BaseModel):
    cars: List[CatalogCarModel]
    total: int
    page: int
    pages: int
    search_links: dict

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

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "user_type": user.user_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user.email)
    user_response = UserResponse(
        id=user_id, email=user.email, name=user.name,
        phone=user.phone, user_type=user.user_type, created_at=user_doc["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"])
    user_response = UserResponse(
        id=user["id"], email=user["email"], name=user["name"],
        phone=user.get("phone"), user_type=user["user_type"], created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"], name=current_user["name"],
        phone=current_user.get("phone"), user_type=current_user["user_type"],
        created_at=current_user["created_at"]
    )

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
    """Get list of all brands in catalog"""
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
    """Search cars in catalog with filters"""
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
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            return {
                **car,
                "search_links": generate_search_links(car["brand"], car["model"])
            }
    raise HTTPException(status_code=404, detail="Car not found in catalog")

@api_router.post("/catalog/{car_id}/add-to-garage")
async def add_catalog_car_to_garage(
    car_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Add car from catalog to user's garage"""
    catalog_car = None
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            catalog_car = car
            break
    
    if not catalog_car:
        raise HTTPException(status_code=404, detail="Car not found in catalog")
    
    # Create garage entry
    garage_id = str(uuid.uuid4())
    garage_doc = {
        "id": garage_id,
        "user_id": current_user["id"],
        "brand": catalog_car["brand"],
        "model": catalog_car["model"],
        "year": catalog_car["year_to"] or catalog_car["year_from"],
        "price_cny": catalog_car["price_from_cny"],
        "engine_type": catalog_car["engine_type"],
        "engine_volume": catalog_car.get("engine_volume"),
        "mileage": None,
        "image_url": catalog_car["image_url"],
        "source_url": None,
        "description": catalog_car["description"],
        "status": "saved",
        "from_catalog": True,
        "catalog_id": car_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.garage.insert_one(garage_doc)
    
    return {"message": "Car added to garage", "garage_id": garage_id}

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
