from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import httpx

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

class CalculatorResult(BaseModel):
    price_cny: float
    price_eur: float
    price_usd: float
    customs_duty: float
    utilization_fee: float
    vat: float
    fixed_costs_byn: float
    fixed_costs_usd: float
    total_byn: float
    total_usd: float
    breakdown: dict

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

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
