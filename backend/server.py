from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
import shutil

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Import modular routes
from routes import auth as auth_routes
from routes import affiliate as affiliate_routes
from routes import user as user_routes
from routes import catalog as catalog_routes

# Import Bitrix24 service
from services.bitrix24 import init_bitrix24, get_bitrix24, Bitrix24Service

# Import Telegram service
from services import telegram_service

# Uploads directory
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

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
# Suppress bcrypt version warning from passlib (passlib 1.7.4 incompatibility with bcrypt 4.x)
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
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
    name: str  # Имя
    last_name: str  # Фамилия
    phone: str  # Телефон (обязательный)
    city: Optional[str] = None  # Город
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
    last_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    user_type: str
    role: str = "user"
    balance: float = 0.0  # Баланс пользователя
    is_verified: bool = False  # Прошёл верификацию
    prepayment_confirmed: bool = False  # Предоплата 500$ подтверждена
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
    year: Optional[int] = None
    price_cny: Optional[float] = 0
    engine_type: Optional[str] = "ice"
    engine_volume: Optional[int] = None
    mileage: Optional[int] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    calculated_price_usd: Optional[float] = None
    calculated_price_byn: Optional[float] = None
    contractors: Optional[dict] = None
    notes: Optional[str] = None
    status: Optional[str] = "saved"
    created_at: Optional[str] = None
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
    car_request: Optional[dict] = None
    application_id: Optional[str] = None
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
    logo_url: Optional[str] = None
    created_at: Optional[str] = None

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

# ==================== IMAGE PROXY ====================

@api_router.get("/proxy/image")
async def proxy_image(url: str):
    """Proxy images from Chinese CDN to bypass CORS restrictions"""
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid image URL")
    
    # Only allow specific domains
    allowed_domains = ["autoimg.cn", "che168.com", "autohome.com", "2sc2.autoimg.cn"]
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    if not any(domain in parsed.netloc for domain in allowed_domains):
        raise HTTPException(status_code=400, detail="Domain not allowed")
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://www.che168.com/"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Image not found")
            
            # Determine content type
            content_type = response.headers.get("content-type", "image/jpeg")
            if "webp" in url:
                content_type = "image/webp"
            elif "png" in url:
                content_type = "image/png"
            elif "jpg" in url or "jpeg" in url:
                content_type = "image/jpeg"
            
            return StreamingResponse(
                BytesIO(response.content),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        logger.error(f"Image proxy error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image")

class TranslateRequest(BaseModel):
    text: str

@api_router.post("/translate")
async def translate_text(request: TranslateRequest):
    """Translate Chinese text to Russian"""
    translated = await Che168API.translate_to_russian(request.text)
    return {"original": request.text, "translated": translated}

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
    
    # Check referral code if provided
    referred_by = None
    referral_code_used = None
    if user.referral_code:
        affiliate = await db.affiliates.find_one({"referral_code": user.referral_code})
        if affiliate:
            referred_by = affiliate["user_id"]
            referral_code_used = user.referral_code
    
    user_id = str(uuid.uuid4())
    full_name = f"{user.name} {user.last_name}"
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "last_name": user.last_name,
        "phone": user.phone,
        "city": user.city,
        "user_type": user.user_type,
        "role": role,
        "balance": 0.0,
        "is_verified": False,
        "prepayment_confirmed": False,
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
        id=user_id, email=user.email, name=user.name, last_name=user.last_name,
        phone=user.phone, city=user.city, user_type=user.user_type, role=role,
        balance=0.0, is_verified=False, prepayment_confirmed=False,
        created_at=user_doc["created_at"]
    )
    
    # Bitrix24: Create contact for new user
    b24 = get_bitrix24()
    if b24:
        try:
            asyncio.create_task(b24.create_contact(
                name=full_name,
                email=user.email,
                phone=user.phone,
                user_type=user.user_type,
                user_id=user_id,
                comments=f"Регистрация на CarBridge. Город: {user.city or 'Не указан'}. Реферал: {referral_code_used or 'Нет'}"
            ))
        except Exception as e:
            logger.error(f"Bitrix24 contact creation error: {e}")
    
    # Telegram: Notify moderators about new user
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            await telegram_service.notify_moderators_new_user(
                moderator_chat_ids,
                full_name,
                user.email,
                user.phone or "Не указан",
                "user"
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
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
        last_name=user.get("last_name"), phone=user.get("phone"), city=user.get("city"),
        user_type=user["user_type"], role=role,
        balance=user.get("balance", 0.0),
        is_verified=user.get("is_verified", False),
        prepayment_confirmed=user.get("prepayment_confirmed", False),
        created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"], name=current_user["name"],
        last_name=current_user.get("last_name"), phone=current_user.get("phone"),
        city=current_user.get("city"), user_type=current_user["user_type"],
        role=current_user.get("role", "user"),
        balance=current_user.get("balance", 0.0),
        is_verified=current_user.get("is_verified", False),
        prepayment_confirmed=current_user.get("prepayment_confirmed", False),
        created_at=current_user["created_at"]
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

@api_router.post("/moderator/users/{user_id}/confirm-prepayment")
async def confirm_user_prepayment(user_id: str, data: dict, current_user: dict = Depends(require_role(["moderator", "admin"]))):
    """Confirm user prepayment of $500"""
    action = data.get("action")  # "approve" or "reject"
    amount = data.get("amount", 500.0)  # Default prepayment amount
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Неверное действие")
    
    prepayment_confirmed = action == "approve"
    
    # Update user document
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "prepayment_confirmed": prepayment_confirmed,
                "prepayment_amount": amount if prepayment_confirmed else 0,
                "prepayment_date": datetime.now(timezone.utc).isoformat(),
                "prepayment_confirmed_by": current_user["id"]
            }
        }
    )
    
    # Update account document
    await db.accounts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "prepayment_confirmed": prepayment_confirmed,
                "prepayment_amount": amount if prepayment_confirmed else 0,
                "prepayment_date": datetime.now(timezone.utc).isoformat(),
                "prepayment_confirmed_by": current_user["id"]
            }
        },
        upsert=True
    )
    
    # Add to balance if prepayment confirmed
    if prepayment_confirmed:
        await db.accounts.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )
    
    # Log moderation action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "prepayment_confirmation",
        "target_type": "user",
        "target_id": user_id,
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", ""),
        "result": "approved" if prepayment_confirmed else "rejected",
        "amount": amount,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Bitrix24: Update contact with prepayment info
    b24 = get_bitrix24()
    if b24 and prepayment_confirmed:
        try:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user:
                asyncio.create_task(b24.create_lead(
                    title=f"Предоплата подтверждена - {user.get('name', '')} {user.get('last_name', '')}",
                    description=f"Клиент внёс предоплату ${amount}. Email: {user.get('email', '')}",
                    contact_email=user.get("email"),
                    contact_phone=user.get("phone"),
                    source="prepayment",
                    user_id=user_id
                ))
        except Exception as e:
            logger.error(f"Bitrix24 lead creation error: {e}")
    
    return {
        "message": f"Предоплата {'подтверждена' if prepayment_confirmed else 'отклонена'}",
        "prepayment_confirmed": prepayment_confirmed,
        "amount": amount if prepayment_confirmed else 0
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

# IMPORTANT: This route must be BEFORE any /moderator/deals/{deal_id} routes
@api_router.get("/moderator/deals/pending-stages")
async def get_deals_pending_moderation_early(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all deals with stages awaiting moderator confirmation"""
    # Find all deals with stages awaiting approval
    deals = await db.deals.find({"status": "active"}, {"_id": 0}).to_list(100)
    
    pending = []
    for deal in deals:
        stages = deal.get("stages", {})
        
        # Handle case where stages might be a list instead of dict
        if isinstance(stages, list):
            continue
        
        if not isinstance(stages, dict):
            continue
            
        user = await db.users.find_one({"id": deal.get("user_id")}, {"_id": 0, "name": 1, "email": 1})
        
        # Check each stage
        for stage_key, stage_data in stages.items():
            if not isinstance(stage_data, dict):
                continue
            
            # Check for stages needing moderation:
            # 1. Locked stages from tender offer that aren't confirmed yet
            # 2. Stages with awaiting_approval flag (manually selected contractor)
            # 3. Stages with pending_review status (client completed and sent for review)
            needs_moderation = False
            
            if stage_data.get("locked") and not stage_data.get("moderator_confirmed") and not stage_data.get("paid"):
                needs_moderation = True
            elif stage_data.get("awaiting_approval") and not stage_data.get("moderator_approved") and not stage_data.get("paid"):
                needs_moderation = True
            elif stage_data.get("status") == "pending_moderation" and not stage_data.get("paid"):
                needs_moderation = True
            elif stage_data.get("status") == "pending_review" and not stage_data.get("paid"):
                needs_moderation = True
            elif stage_data.get("status") == "awaiting_approval" and not stage_data.get("moderator_approved") and not stage_data.get("paid"):
                needs_moderation = True
            
            if needs_moderation and stage_data.get("contractor_id"):
                pending.append({
                    "deal_id": deal["id"],
                    "car_info": deal.get("car_info", {}),
                    "user": user,
                    "stage_key": stage_key,
                    "contractor_id": stage_data.get("contractor_id"),
                    "contractor_name": stage_data.get("contractor_name"),
                    "price": stage_data.get("price"),
                    "status": stage_data.get("status"),
                    "is_from_tender": stage_data.get("locked", False),
                    "assigned_at": stage_data.get("assigned_at"),
                    "review_requested_at": stage_data.get("review_requested_at"),
                    "created_at": deal.get("created_at")
                })
    
    return pending

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

@api_router.get("/deals/completed")
async def get_completed_deals(current_user: dict = Depends(get_current_user)):
    """Get all completed deals (purchased cars) for user"""
    completed_deals = await db.deals.find(
        {"user_id": current_user["id"], "status": "completed"},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(100)
    
    # Enrich with car info
    for deal in completed_deals:
        if deal.get("car_id"):
            car = await db.garage.find_one({"id": deal["car_id"]}, {"_id": 0})
            if car:
                deal["car_details"] = car
    
    return completed_deals

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
            "image_url": car.get("image_url")
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

@api_router.post("/deals/{deal_id}/update-stage-price")
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

@api_router.get("/deals/{deal_id}/messages")
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

@api_router.post("/deals/{deal_id}/messages")
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

@api_router.get("/deals/{deal_id}/files")
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

@api_router.post("/deals/{deal_id}/files")
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

@api_router.get("/deals/{deal_id}/files/{file_id}/download")
async def download_deal_file(deal_id: str, file_id: str, current_user: dict = Depends(get_current_user)):
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

@api_router.delete("/deals/{deal_id}/files/{file_id}")
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

@api_router.get("/contractor/deals/{deal_id}/messages")
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

@api_router.post("/contractor/deals/{deal_id}/messages")
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

@api_router.get("/contractor/deals/{deal_id}/files")
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

@api_router.post("/contractor/deals/{deal_id}/files")
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

@api_router.get("/contractor/deals/{deal_id}/files/{file_id}/download")
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

@api_router.get("/contractor/deals")
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

@api_router.get("/deals/{deal_id}/stages/{stage_key}/messages")
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

@api_router.post("/deals/{deal_id}/stages/{stage_key}/messages")
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

@api_router.get("/deals/{deal_id}/stages/{stage_key}/files")
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

@api_router.post("/deals/{deal_id}/stages/{stage_key}/files")
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
@api_router.get("/contractor/deals/{deal_id}/stages/{stage_key}/messages")
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

@api_router.post("/contractor/deals/{deal_id}/stages/{stage_key}/messages")
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

@api_router.post("/contractor/deals/{deal_id}/stages/{stage_key}/files")
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
@api_router.get("/contractor/deals/{deal_id}/my-stages")
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
@api_router.get("/deals/{deal_id}/unread-counts")
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

@api_router.get("/contractor/deals/{deal_id}/unread-counts")
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
@api_router.post("/deals/{deal_id}/stages/{stage_key}/complete")
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

@api_router.delete("/deals/{deal_id}")
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

@api_router.post("/legal-help/request")
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

@api_router.get("/legal-help/requests")
async def get_legal_help_requests(current_user: dict = Depends(get_current_user)):
    """Get user's legal help requests"""
    requests = await db.legal_requests.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return requests

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
    
    # Check prepayment status from user or account
    prepayment_confirmed = current_user.get("prepayment_confirmed", False)
    if account:
        prepayment_confirmed = account.get("prepayment_confirmed", prepayment_confirmed)
    
    # Check if user can perform actions (verification + prepayment + application filled)
    is_verified = current_user.get("is_verified", False)
    if account:
        is_verified = account.get("is_verified", is_verified)
    
    contract_signed = verification.get("contract_signed", False) if verification else False
    
    # User can perform actions only if verified AND prepayment confirmed
    can_perform_actions = is_verified and prepayment_confirmed and contract_signed
    
    return {
        "balance": account.get("balance", 0) if account else current_user.get("balance", 0),
        "is_verified": is_verified,
        "prepayment_confirmed": prepayment_confirmed,
        "verification_status": verification.get("status") if verification else "not_started",
        "contract_signed": contract_signed,
        "contract_number": verification.get("contract_number") if verification else None,
        "can_perform_actions": can_perform_actions,
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

@api_router.get("/affiliate/status")
async def get_affiliate_status(current_user: dict = Depends(get_current_user)):
    """Get current user's affiliate status with detailed stats"""
    affiliate = await db.affiliates.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not affiliate:
        raise HTTPException(status_code=404, detail="Вы не зарегистрированы в партнёрской программе")
    
    # Get referrals with their deal stats
    referrals = await db.referrals.find(
        {"affiliate_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    
    # Calculate stats
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
    
    # Calculate Belarus price automatically
    calculated_price_usd = None
    calculated_price_byn = None
    
    try:
        current_year = datetime.now().year
        car_age = current_year - car.year
        age_category = "under3" if car_age < 3 else ("3to5" if car_age < 5 else "over5")
        engine_volume = car.engine_volume or 2000
        
        calc_input = CalculatorInput(
            price_cny=car.price_cny,
            age=age_category,
            engine_type=car.engine_type,
            engine_volume=engine_volume if car.engine_type != "electric" else 0,
            user_type="individual",
            use_decree_140=False,
            payment_via_platform=True
        )
        calc_result = await calculate_customs(calc_input)
        calculated_price_usd = calc_result.total_usd
        calculated_price_byn = calc_result.total_byn
        logger.info(f"Calculated price for {car.brand} {car.model}: ${calculated_price_usd} / {calculated_price_byn} BYN")
    except Exception as e:
        logger.error(f"Price calculation error: {e}")
    
    car_doc = {
        "id": car_id,
        "user_id": current_user["id"],
        **car.model_dump(),
        "calculated_price_usd": calculated_price_usd,
        "calculated_price_byn": calculated_price_byn,
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
            calc_result = await calculate_customs(calc_input)
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
    
    # Bitrix24: Create deal for new tender
    b24 = get_bitrix24()
    if b24:
        try:
            asyncio.create_task(b24.create_deal(
                title=f"Тендер: {car.get('brand', '')} {car.get('model', '')} {car.get('year', '')}",
                contact_email=current_user.get("email"),
                car_brand=car.get("brand"),
                car_model=car.get("model"),
                car_year=car.get("year"),
                price_usd=car.get("price_cny", 0) / 7.2 if car.get("price_cny") else None,
                tender_id=tender_id,
                stage="NEW",
                comments=f"Тендер создан на CarBridge. Пробег: {car.get('mileage', 'N/A')} км"
            ))
            # Create task for manager
            asyncio.create_task(b24.create_task(
                title=f"Новый тендер: {car.get('brand', '')} {car.get('model', '')}",
                description=f"Клиент: {current_user.get('name', current_user.get('email'))}\n"
                           f"Авто: {car.get('brand', '')} {car.get('model', '')} {car.get('year', '')}\n"
                           f"ID тендера: {tender_id}",
                deadline_days=1,
                priority=2  # High
            ))
        except Exception as e:
            logger.error(f"Bitrix24 tender deal creation error: {e}")
    
    # Send notifications to all approved contractors
    try:
        approved_contractors = await db.contractors.find({"status": "approved"}, {"_id": 0}).to_list(100)
        for contractor in approved_contractors:
            notification_doc = {
                "id": str(uuid.uuid4()),
                "contractor_id": contractor["id"],
                "type": "new_tender",
                "title": "Новый тендер",
                "message": f"Появился новый тендер на {car.get('brand', 'авто')} {car.get('model', '')}",
                "tender_id": tender_id,
                "car_info": {
                    "brand": car.get("brand"),
                    "model": car.get("model"),
                    "year": car.get("year"),
                    "price_cny": car.get("price_cny")
                },
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notification_doc)
        logger.info(f"Tender {tender_id} created from garage, notifications sent to {len(approved_contractors)} contractors")
    except Exception as e:
        logger.error(f"Error sending tender notifications: {e}")
    
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
    
    # Enrich each tender with real contractor offers from tender_offers collection
    for tender in tenders:
        real_offers = await db.tender_offers.find(
            {"tender_id": tender["id"]},
            {"_id": 0}
        ).to_list(50)
        
        # Merge mock offers with real offers (real offers take priority)
        existing_offers = tender.get("offers", [])
        tender["offers"] = real_offers + existing_offers
        tender["offers_count"] = len(tender["offers"])
    
    return [TenderResponse(**t) for t in tenders]

@api_router.get("/tenders/{tender_id}", response_model=TenderResponse)
async def get_tender(tender_id: str, current_user: dict = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id, "user_id": current_user["id"]}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Get real contractor offers from tender_offers collection
    real_offers = await db.tender_offers.find(
        {"tender_id": tender_id},
        {"_id": 0}
    ).to_list(50)
    
    # Merge mock offers with real offers (real offers first)
    existing_offers = tender.get("offers", [])
    tender["offers"] = real_offers + existing_offers
    tender["offers_count"] = len(tender["offers"])
    
    return TenderResponse(**tender)

@api_router.post("/tenders/{tender_id}/select/{offer_id}")
async def select_offer(tender_id: str, offer_id: str, current_user: dict = Depends(get_current_user)):
    tender = await db.tenders.find_one({"id": tender_id, "user_id": current_user["id"]}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Check in mock offers first
    offer_exists = any(o["id"] == offer_id for o in tender.get("offers", []))
    
    # Also check in real contractor offers
    real_offer = None
    if not offer_exists:
        real_offer = await db.tender_offers.find_one({"id": offer_id, "tender_id": tender_id}, {"_id": 0})
        offer_exists = real_offer is not None
    
    if not offer_exists:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    await db.tenders.update_one(
        {"id": tender_id},
        {"$set": {"selected_offer_id": offer_id, "status": "selected"}}
    )
    
    # Update the offer status to accepted
    if real_offer:
        await db.tender_offers.update_one(
            {"id": offer_id},
            {"$set": {"status": "accepted"}}
        )
        
        # Send Telegram notification to contractor about accepted offer
        contractor_id = real_offer.get("contractor_id")
        if contractor_id:
            contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0, "telegram_chat_id": 1})
            if contractor and contractor.get("telegram_chat_id"):
                car_info = tender.get("car_info", {}) or tender.get("car_request", {})
                car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "Авто"
                stages = real_offer.get("services", [])
                client_name = current_user.get("name", "Клиент")
                await telegram_service.notify_tender_offer_accepted(
                    contractor["telegram_chat_id"],
                    car_name,
                    stages,
                    client_name
                )
    
    # Update car status
    if tender.get("car_id"):
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

@api_router.get("/contractors/approved", response_model=List[ContractorResponse])
async def get_approved_contractors():
    """Get all approved and verified contractors for direct selection"""
    # Get verified contractors from database
    query = {"status": "approved", "verified": True}
    
    db_contractors = await db.contractors.find(query, {"_id": 0, "password_hash": 0}).to_list(100)
    
    # Add name field from company_name if missing
    for c in db_contractors:
        c["name"] = c.get("name") or c.get("company_name")
        services = c.get("services", [])
        if isinstance(services, list):
            c["services"] = ", ".join(services)
    
    # Add demo contractors
    demo_ids = {c["id"] for c in db_contractors}
    demo_emails = {c.get("email") for c in db_contractors if c.get("email")}
    demo_filtered = [c for c in DEMO_CONTRACTORS if c["id"] not in demo_ids and c.get("email") not in demo_emails]
    
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

MANAGER_HELP_COST = 200  # USD (deprecated - now free with prepayment)

@api_router.post("/help-requests")
async def create_help_request(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a general help request (free with prepayment)"""
    # Check if user has verified and paid prepayment
    if not current_user.get("prepayment_confirmed"):
        account = await db.accounts.find_one({"user_id": current_user["id"]})
        if not account or not account.get("prepayment_confirmed"):
            raise HTTPException(
                status_code=403, 
                detail="Для запроса помощи менеджера необходимо внести предоплату $500"
            )
    
    request_type = data.get("request_type", "general")
    car_id = data.get("car_id")
    car_details = data.get("car_details", {})
    description = data.get("description", "")
    
    request_id = str(uuid.uuid4())
    help_request = {
        "id": request_id,
        "user_id": current_user["id"],
        "user_name": f"{current_user.get('name', '')} {current_user.get('last_name', '')}",
        "user_email": current_user.get("email"),
        "user_phone": current_user.get("phone"),
        "request_type": request_type,
        "car_id": car_id,
        "car_details": car_details,
        "description": description,
        "status": "pending",
        "assigned_manager_id": None,
        "assigned_manager_name": None,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.help_requests.insert_one(help_request)
    
    # Update car if car_id provided
    if car_id:
        await db.garage.update_one(
            {"id": car_id},
            {"$set": {
                "manager_help_requested": True, 
                "manager_help_request_id": request_id
            }}
        )
    
    # Bitrix24: Create lead for manager help request
    b24 = get_bitrix24()
    if b24:
        try:
            asyncio.create_task(b24.create_lead(
                title=f"Запрос помощи менеджера - {current_user.get('name', '')} {current_user.get('last_name', '')}",
                description=f"Тип: {request_type}\nОписание: {description}\n\nАвто: {car_details}",
                contact_email=current_user.get("email"),
                contact_phone=current_user.get("phone"),
                source="manager_help",
                user_id=current_user["id"]
            ))
        except Exception as e:
            logger.error(f"Bitrix24 lead creation error: {e}")
    
    return {
        "message": "Запрос на помощь менеджера отправлен",
        "request_id": request_id
    }

@api_router.get("/help-requests")
async def get_user_help_requests(current_user: dict = Depends(get_current_user)):
    """Get current user's help requests"""
    requests = await db.help_requests.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return requests

@api_router.get("/help-requests/{request_id}")
async def get_help_request(request_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific help request with chat history"""
    request = await db.help_requests.find_one(
        {"id": request_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    return request

@api_router.post("/help-requests/{request_id}/messages")
async def send_help_request_message(
    request_id: str, 
    data: dict, 
    current_user: dict = Depends(get_current_user)
):
    """Send a message in a help request chat"""
    request = await db.help_requests.find_one(
        {"id": request_id, "user_id": current_user["id"]}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    
    message = {
        "id": str(uuid.uuid4()),
        "sender_id": current_user["id"],
        "sender_name": f"{current_user.get('name', '')} {current_user.get('last_name', '')}",
        "sender_type": "user",
        "content": data.get("content", ""),
        "attachments": data.get("attachments", []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.help_requests.update_one(
        {"id": request_id},
        {"$push": {"messages": message}}
    )
    
    return {"message": "Сообщение отправлено", "message_data": message}

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
    
    # Telegram: Notify moderators about manager help request
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            car_info = f"{car.get('brand', '')} {car.get('model', '')}".strip() or "Авто"
            await telegram_service.notify_moderators_manager_help_request(
                moderator_chat_ids,
                current_user.get("name", "Клиент"),
                current_user.get("email", ""),
                current_user.get("phone", ""),
                car_info
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
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

# ==================== MODERATOR: CAR APPLICATIONS (User requests) ====================

@api_router.get("/moderator/car-applications")
async def get_car_applications(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all car applications (user requests for car selection)"""
    applications = await db.applications.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with user data
    result = []
    for app in applications:
        user = await db.users.find_one({"id": app.get("user_id")}, {"_id": 0, "name": 1, "email": 1})
        app["user_name"] = user.get("name", "Unknown") if user else "Unknown"
        app["user_email"] = user.get("email", "") if user else ""
        result.append(app)
    
    return result

@api_router.delete("/moderator/car-applications/{app_id}")
async def delete_car_application(app_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Delete a car application"""
    result = await db.applications.delete_one({"id": app_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Car application deleted"}

# ==================== MODERATOR: DELETE ENDPOINTS ====================

@api_router.delete("/moderator/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_role(["admin"]))):
    """Delete a user and all related data (admin only)"""
    # Check user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting admins
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin users")
    
    # Delete related data
    await db.garage.delete_many({"user_id": user_id})
    await db.applications.delete_many({"user_id": user_id})
    await db.verifications.delete_many({"user_id": user_id})
    await db.chat_history.delete_many({"user_id": user_id})
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    return {"message": "User and all related data deleted"}

@api_router.delete("/moderator/tenders/{tender_id}")
async def delete_tender(tender_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Delete a tender"""
    # Find garage item with this tender
    garage_item = await db.garage.find_one({"tender_id": tender_id})
    if garage_item:
        # Remove tender from garage item
        await db.garage.update_one(
            {"id": garage_item["id"]},
            {"$set": {"status": "in_garage", "tender_id": None}}
        )
    
    # Delete tender and its offers
    await db.tenders.delete_one({"id": tender_id})
    await db.tender_offers.delete_many({"tender_id": tender_id})
    
    return {"message": "Tender deleted"}

@api_router.delete("/moderator/garage/{garage_id}")
async def delete_garage_item(garage_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Delete a car from user's garage"""
    result = await db.garage.delete_one({"id": garage_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Garage item not found")
    return {"message": "Garage item deleted"}

@api_router.delete("/moderator/contractors/{contractor_id}")
async def delete_contractor(contractor_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Delete a contractor"""
    # Delete contractor
    result = await db.contractors.delete_one({"id": contractor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # Delete related contractor application
    await db.contractor_applications.delete_many({"contractor_id": contractor_id})
    
    return {"message": "Contractor deleted"}

@api_router.delete("/moderator/deals/{deal_id}")
async def delete_deal(deal_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Delete a deal (resets garage item to normal state)"""
    # Find and update garage item
    result = await db.garage.update_one(
        {"id": deal_id},
        {"$set": {
            "status": "in_garage",
            "current_stage": None,
            "completed_stages": [],
            "tender_id": None,
            "selected_contractor_id": None
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return {"message": "Deal cancelled and reset to garage"}

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
    """Confirm a stage of a deal - enables client to pay"""
    stage_key = stage.get("stage")
    if not stage_key:
        raise HTTPException(status_code=400, detail="Stage key required")
    
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    stages = deal.get("stages", {})
    if stage_key not in stages:
        raise HTTPException(status_code=400, detail=f"Stage {stage_key} not found in deal")
    
    # Update stage to confirmed by moderator - enables payment
    await db.deals.update_one(
        {"id": deal_id},
        {"$set": {
            f"stages.{stage_key}.moderator_confirmed": True,
            f"stages.{stage_key}.moderator_approved": True,
            f"stages.{stage_key}.awaiting_approval": False,
            f"stages.{stage_key}.status": "approved",
            f"stages.{stage_key}.moderator_id": current_user["id"],
            f"stages.{stage_key}.confirmed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log moderation action
    await db.moderation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "deal_id": deal_id,
        "stage_key": stage_key,
        "action": "approve_stage",
        "moderator_id": current_user["id"],
        "moderator_name": current_user.get("name", current_user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Create notification for client
    stage_labels = {
        "leasing": "Лизинг",
        "inspection": "Инспекция авто",
        "export": "Выкуп и экспорт",
        "logistics_china": "Доставка до порта (Китай)",
        "insurance": "Страхование авто",
        "delivery_rb": "Доставка в Беларусь",
        "customs": "Таможенное оформление",
        "completion": "Завершение сделки"
    }
    stage_label = stage_labels.get(stage_key, stage_key)
    car_info = deal.get("car_info", {})
    car_name = f"{car_info.get('brand', '')} {car_info.get('model', '')}".strip() or "авто"
    
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": deal["user_id"],
        "type": "stage_approved",
        "title": "Этап одобрен",
        "message": f"Этап «{stage_label}» для {car_name} одобрен модератором. Теперь вы можете оплатить этап.",
        "deal_id": deal_id,
        "stage_key": stage_key,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_notifications.insert_one(notification)
    
    # Send Telegram notification to client
    user = await db.users.find_one({"id": deal["user_id"]}, {"_id": 0, "telegram_chat_id": 1})
    if user and user.get("telegram_chat_id"):
        await telegram_service.notify_moderator_action(
            user["telegram_chat_id"],
            car_name,
            stage_key,
            "approved"
        )
    
    return {"message": f"Этап '{stage_key}' подтверждён модератором"}

# Moderator endpoints for viewing stage messages and files
@api_router.get("/moderator/deals/{deal_id}/stages/{stage_key}/messages")
async def get_moderator_stage_messages(deal_id: str, stage_key: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get messages for a specific stage (moderator view)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    messages = await db.deal_messages.find(
        {"deal_id": deal_id, "stage_key": stage_key},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return messages

@api_router.get("/moderator/deals/{deal_id}/stages/{stage_key}/files")
async def get_moderator_stage_files(deal_id: str, stage_key: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get files for a specific stage (moderator view)"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    files = await db.deal_files.find(
        {"deal_id": deal_id, "stage_key": stage_key},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return files

@api_router.get("/moderator/deals/{deal_id}/files/{file_id}/download")
async def download_moderator_deal_file(deal_id: str, file_id: str, current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Download a file from a deal (moderator)"""
    file_doc = await db.deal_files.find_one({"id": file_id, "deal_id": deal_id}, {"_id": 0})
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

@api_router.get("/moderator/tenders")
async def get_all_tenders_moderator(current_user: dict = Depends(require_role(["admin", "moderator"]))):
    """Get all tenders for moderator"""
    tenders = await db.tenders.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for tender in tenders:
        car_id = tender.get("car_id") or tender.get("garage_id")
        car = None
        if car_id:
            car = await db.garage.find_one({"id": car_id}, {"_id": 0})
        
        result.append({
            "id": tender["id"],
            "car_id": car_id,
            "car_brand": car["brand"] if car else tender.get("brand", "Unknown"),
            "car_model": car["model"] if car else tender.get("model", "Unknown"),
            "budget": car.get("calculated_price_usd", 0) if car else tender.get("budget", 0),
            "offers_count": len(tender.get("offers", [])),
            "status": tender.get("status", "active"),
            "created_at": tender.get("created_at", "")
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
    
    # Get current catalog data for recommendations
    catalog_summary = ""
    try:
        catalog_data = await Che168API.search_cars(page=1, per_page=50)
        if catalog_data.get("cars"):
            brands_available = list(set(c["brand"] for c in catalog_data["cars"]))
            price_range = [c["price_from_cny"] for c in catalog_data["cars"] if c.get("price_from_cny")]
            min_price = min(price_range) if price_range else 0
            max_price = max(price_range) if price_range else 0
            catalog_summary = f"""
АКТУАЛЬНЫЕ ДАННЫЕ КАТАЛОГА CHE168:
- Доступные марки: {', '.join(brands_available[:15])}
- Диапазон цен: ¥{min_price:,.0f} - ¥{max_price:,.0f} юаней
- Всего объявлений: более {catalog_data.get('total', 100)}
"""
    except Exception as e:
        logger.error(f"Failed to get catalog summary: {e}")
    
    system_message = f"""Ты - AI-консультант платформы CARBRIDGE по подбору автомобилей из Китая.

ТВОЯ ГЛАВНАЯ ЗАДАЧА: Провести клиента через опрос для подбора авто, собрать его требования и предложить подходящие варианты.

{catalog_summary}

СТРУКТУРА ОПРОСА (задавай вопросы последовательно, по 1-2 за раз):

📋 ЭТАП 1 - ЗНАКОМСТВО:
- Представься и спроси имя клиента
- Уточни город доставки

📋 ЭТАП 2 - ОСНОВНЫЕ ТРЕБОВАНИЯ:
- Какую марку/модель рассматривает? (или "любую")
- Год выпуска: от какого года?
- Тип кузова: седан, кроссовер, хэтчбек, минивэн, пикап?
- Тип двигателя: бензин, дизель, электро, гибрид?

📋 ЭТАП 3 - ДЕТАЛИ:
- Коробка передач: механика, автомат, робот, вариатор?
- Привод: передний, задний, полный?
- Предпочтения по цвету кузова и салона?

📋 ЭТАП 4 - СОСТОЯНИЕ:
- Новый или с пробегом?
- Максимальный пробег (если б/у)?
- Допустимы ли мелкие повреждения?

📋 ЭТАП 5 - БЮДЖЕТ:
- Бюджет в юанях/долларах (цена в Китае)?
- Или общий бюджет с доставкой и таможней?
- Срочность покупки?

📋 ЭТАП 6 - ПРИОРИТЕТЫ (от 1 до 5):
- Что важнее: цена, надёжность, технологичность, престиж, экономичность?

ВАЖНЫЕ ПРАВИЛА:
1. После каждого ответа клиента КРАТКО подтверди понимание и задай следующий вопрос
2. Когда соберёшь основные данные (марка/кузов, бюджет, год) - ОБЯЗАТЕЛЬНО предложи 5 вариантов авто
3. Формат рекомендаций:

🚗 ПОДОБРАННЫЕ ВАРИАНТЫ:
1. [Марка Модель] - ¥[цена] ([год] г., [пробег] км, [тип двигателя])
2. ...

4. После рекомендаций ВСЕГДА предлагай:
   - "Хотите посмотреть детали любого авто? Перейдите в каталог: /catalog"
   - "Готовы оформить заявку? Зарегистрируйтесь и создайте заявку в личном кабинете: /dashboard/applications"

5. Если клиент согласен на заявку, дай краткую инструкцию:
   "Для создания заявки:
   1. Войдите в личный кабинет (/auth)
   2. Перейдите в раздел 'Заявки' 
   3. Нажмите 'Новая заявка' и заполните форму
   Наш менеджер свяжется с вами в течение 24 часов!"

СТИЛЬ ОБЩЕНИЯ:
- Дружелюбный, профессиональный
- Краткие ответы (2-4 предложения + вопрос)
- Используй эмодзи умеренно
- Отвечай ТОЛЬКО на русском языке"""

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
        
        # Check if user is asking for car recommendations
        user_text = message.message.lower()
        car_context = ""
        
        # If user mentions budget or specific requirements, search catalog
        if any(word in user_text for word in ['бюджет', 'цена', 'юаней', 'долларов', 'подбери', 'покажи', 'варианты', 'рекомендуй']):
            try:
                # Parse potential filters from message
                search_params = {}
                
                # Try to extract brand
                brands = ['byd', 'geely', 'changan', 'haval', 'chery', 'nio', 'li auto', 'xpeng', 'jac', 'dfsk', 'faw', 'gac', 'saic']
                for brand in brands:
                    if brand in user_text:
                        search_params['mark'] = brand.upper()
                        break
                
                # Search catalog
                catalog_results = await Che168API.search_cars(**search_params, page=1, per_page=10)
                
                if catalog_results.get("cars"):
                    cars = catalog_results["cars"][:5]
                    car_context = "\n\nАКТУАЛЬНЫЕ АВТО ИЗ КАТАЛОГА CHE168 (используй для рекомендаций):\n"
                    for i, car in enumerate(cars, 1):
                        mileage = f"{car.get('mileage', 0):,} км" if car.get('mileage') else "новый"
                        engine = {'electric': 'электро', 'hybrid': 'гибрид', 'ice': 'бензин'}.get(car.get('engine_type', ''), '')
                        car_context += f"{i}. {car['brand']} {car['model']} - ¥{car['price_from_cny']:,.0f} ({car['year_from']} г., {mileage}, {engine}) ID: {car['id']}\n"
            except Exception as e:
                logger.error(f"Catalog search for chat failed: {e}")
        
        # Add history to chat context
        for h in history:
            if h["role"] == "user":
                await chat.send_message(UserMessage(text=h["content"]))
        
        # Send message with car context if available
        full_message = message.message
        if car_context:
            full_message = f"{message.message}\n{car_context}"
        
        user_msg = UserMessage(text=full_message)
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
2. Посмотреть каталог авто: /catalog
3. Создать заявку в личном кабинете: /dashboard/applications

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
    
    # Telegram: Notify moderators about verification request
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            await telegram_service.notify_moderators_verification_request(
                moderator_chat_ids,
                data.full_name,
                data.email,
                data.phone
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
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
    
    # Bitrix24: Create lead for new application
    b24 = get_bitrix24()
    if b24:
        try:
            asyncio.create_task(b24.create_lead(
                title=f"Заявка на {data.brand or 'авто'} {data.model or ''} - {application_number}",
                contact_name=data.full_name or current_user.get("name", ""),
                email=data.email or current_user.get("email", ""),
                phone=data.phone or current_user.get("phone"),
                car_brand=data.brand,
                car_model=data.model,
                budget_min=data.budget_china_from or data.budget_min,
                budget_max=data.budget_china_to or data.budget_max,
                application_id=application_id,
                comments=f"Год: {data.year_from}-{data.year_to}, Двигатель: {data.engine_type}, Город: {data.delivery_city}",
                source="Заявка на авто - CarBridge"
            ))
        except Exception as e:
            logger.error(f"Bitrix24 lead creation error: {e}")
    
    # Telegram: Notify moderators about new application
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            budget = f"${data.budget_china_from or data.budget_min or 0} - ${data.budget_china_to or data.budget_max or 0}"
            await telegram_service.notify_moderators_new_application(
                moderator_chat_ids,
                data.full_name or current_user.get("name", "Клиент"),
                data.brand or "Не указано",
                data.model or "",
                budget
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
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
    
    # Enrich with contractor offers
    for app in applications:
        offers = await db.tender_offers.find(
            {"application_id": app["id"]},
            {"_id": 0}
        ).to_list(50)
        app["offers"] = offers
        app["offers_count"] = len(offers)
    
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
    
    # Get contractor offers for this application
    offers = await db.tender_offers.find(
        {"application_id": application_id},
        {"_id": 0}
    ).to_list(50)
    application["offers"] = offers
    application["offers_count"] = len(offers)
    
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
    
    # Send notifications to all approved contractors
    approved_contractors = await db.contractors.find({"status": "approved"}, {"_id": 0}).to_list(100)
    for contractor in approved_contractors:
        notification_doc = {
            "id": str(uuid.uuid4()),
            "contractor_id": contractor["id"],
            "type": "new_tender",
            "title": "Новый тендер",
            "message": f"Появился новый тендер на {app.get('brand', 'авто')} {app.get('model', '')}",
            "tender_id": tender_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification_doc)
        
        # Send Telegram notification to contractor
        if contractor.get("telegram_chat_id"):
            await telegram_service.notify_new_tender(
                contractor["telegram_chat_id"],
                app.get('brand', 'Авто'),
                app.get('model', ''),
                app.get('budget_min'),
                app.get('budget_max'),
                app.get('stages', [])
            )
    
    logger.info(f"Tender {tender_id} created, notifications sent to {len(approved_contractors)} contractors")
    
    # Telegram: Notify moderators about new tender
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            budget = f"${app.get('budget_min', 0)} - ${app.get('budget_max', 0)}"
            await telegram_service.notify_moderators_new_tender(
                moderator_chat_ids,
                current_user.get("name", "Клиент"),
                app.get('brand', 'Не указано'),
                app.get('model', ''),
                budget
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
    return {"message": "Тендер запущен", "tender_id": tender_id}

@api_router.post("/applications/{application_id}/select-contractor")
async def select_contractor_directly(application_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Select a contractor directly for application (without tender)"""
    contractor_id = data.get("contractor_id")
    if not contractor_id:
        raise HTTPException(status_code=400, detail="contractor_id required")
    
    # Check application
    app = await db.applications.find_one({"id": application_id, "user_id": current_user["id"]})
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if app.get("tender_started"):
        raise HTTPException(status_code=400, detail="Тендер уже запущен, используйте раздел Тендеры")
    
    # Check contractor
    contractor = await db.contractors.find_one({"id": contractor_id, "status": "approved"})
    if not contractor:
        raise HTTPException(status_code=404, detail="Подрядчик не найден")
    
    # Create a deal directly
    deal_id = str(uuid.uuid4())
    
    # Get all contractor's services as default stages
    contractor_services = contractor.get("services", [])
    if isinstance(contractor_services, str):
        contractor_services = [s.strip() for s in contractor_services.split(",") if s.strip()]
    
    # Standard stages mapping
    stage_mapping = {
        "leasing": "Лизинг",
        "inspection": "Инспекция авто",
        "export": "Выкуп и экспорт",
        "logistics_china": "Доставка до порта(Китай)",
        "insurance": "Страхование авто",
        "delivery_rb": "Доставка в Беларусь",
        "customs": "Таможенное оформление",
        "completion": "Завершение сделки"
    }
    
    # Create deal stages based on contractor services
    deal_stages = []
    for svc in contractor_services:
        if svc in stage_mapping:
            # Get price - handle both numeric and dict formats (for leasing)
            price_data = contractor.get("service_prices", {}).get(svc, 0)
            if isinstance(price_data, dict):
                # For leasing, price might be a rate object
                price = price_data.get("rate", 0)
            else:
                price = price_data if isinstance(price_data, (int, float)) else 0
            
            deal_stages.append({
                "name": stage_mapping[svc],
                "key": svc,
                "contractor_id": contractor_id,
                "contractor_name": contractor["company_name"],
                "price": price,
                "status": "pending",  # pending, confirmed_by_moderator, paid, completed
                "locked": True,  # Cannot change contractor for pre-selected stages
                "documents": [],
                "messages": []
            })
    
    deal = {
        "id": deal_id,
        "user_id": current_user["id"],
        "application_id": application_id,
        "contractor_id": contractor_id,
        "contractor_name": contractor["company_name"],
        "car_info": {
            "brand": app.get("brand"),
            "model": app.get("model"),
            "year_from": app.get("year_from"),
            "year_to": app.get("year_to")
        },
        "stages": deal_stages,
        "current_stage_index": 0,
        "status": "active",
        "total_amount": sum(s.get("price", 0) for s in deal_stages),
        "paid_amount": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deals.insert_one(deal)
    
    # Update application
    await db.applications.update_one(
        {"id": application_id},
        {"$set": {
            "status": "in_deal",
            "deal_id": deal_id,
            "selected_contractor_id": contractor_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create initial document exchange card
    doc_card = {
        "id": str(uuid.uuid4()),
        "deal_id": deal_id,
        "user_id": current_user["id"],
        "contractor_id": contractor_id,
        "type": "deal_documents",
        "title": f"Документы по сделке: {app.get('brand', '')} {app.get('model', '')}",
        "files": [],
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deal_documents.insert_one(doc_card)
    
    # Bitrix24: Create deal and task
    b24 = get_bitrix24()
    if b24:
        try:
            # Create deal in Bitrix24
            asyncio.create_task(b24.create_deal(
                title=f"Сделка: {app.get('brand', '')} {app.get('model', '')} - {contractor['company_name']}",
                contact_email=current_user.get("email"),
                car_brand=app.get("brand"),
                car_model=app.get("model"),
                price_usd=deal["total_amount"],
                deal_id=deal_id,
                contractor_name=contractor["company_name"],
                stage="EXECUTING",
                comments=f"Подрядчик выбран напрямую из заявки. Этапов: {len(deal_stages)}"
            ))
            # Create task for contractor follow-up
            asyncio.create_task(b24.create_task(
                title=f"Новая сделка: {app.get('brand', '')} {app.get('model', '')}",
                description=f"Клиент: {current_user.get('name', current_user.get('email'))}\n"
                           f"Подрядчик: {contractor['company_name']}\n"
                           f"Сумма: ${deal['total_amount']}\n"
                           f"ID сделки: {deal_id}",
                deadline_days=2,
                priority=2  # High
            ))
            # Notify in chat
            asyncio.create_task(b24.send_notification(
                user_id=1,  # Admin
                message=f"🚗 Новая сделка на CarBridge!\n"
                       f"Клиент: {current_user.get('name', current_user.get('email'))}\n"
                       f"Авто: {app.get('brand', '')} {app.get('model', '')}\n"
                       f"Подрядчик: {contractor['company_name']}\n"
                       f"Сумма: ${deal['total_amount']}"
            ))
        except Exception as e:
            logger.error(f"Bitrix24 deal creation error: {e}")
    
    return {
        "message": "Подрядчик выбран, сделка создана",
        "deal_id": deal_id,
        "contractor_name": contractor["company_name"]
    }

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
    
    # Telegram: Notify moderators about new contractor
    try:
        moderator_chat_ids = await get_moderator_chat_ids()
        if moderator_chat_ids:
            services_text = ", ".join(data.services) if data.services else "Не указаны"
            await telegram_service.notify_moderators_contractor_approval(
                moderator_chat_ids,
                data.company_name,
                data.services[0] if data.services else "Не указан",
                data.email,
                services_text
            )
    except Exception as e:
        logger.error(f"Telegram moderator notification error: {e}")
    
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
        "contractor_rating": contractor.get("rating", 5.0),
        "tender_id": tender_id,
        "application_id": application_id,
        "price_usd": data.get("price_usd"),
        "price_cny": data.get("price_cny"),
        "delivery_days": data.get("delivery_days"),
        "delivery_cost": data.get("delivery_cost"),
        "car_details": data.get("car_details"),
        "car_link": data.get("car_link"),
        "car_photos": data.get("car_photos", []),
        "car_videos": data.get("car_videos", []),
        "notes": data.get("notes"),
        "valid_until": data.get("valid_until"),
        "included_services": data.get("included_services", {}),
        "service_prices": data.get("service_prices", {}),
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

# ==================== USER/CLIENT NOTIFICATIONS ====================

@api_router.get("/user/notifications")
async def get_user_notifications(current_user: dict = Depends(get_current_user)):
    """Get notifications for the current user/client"""
    notifications = await db.user_notifications.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    unread_count = len([n for n in notifications if not n.get("is_read")])
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@api_router.post("/user/notifications/{notification_id}/read")
async def mark_user_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark user notification as read"""
    await db.user_notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Уведомление отмечено как прочитанное"}

@api_router.post("/user/notifications/read-all")
async def mark_all_user_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    await db.user_notifications.update_many(
        {"user_id": current_user["id"], "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Все уведомления отмечены как прочитанные"}

# ==================== CONTRACTOR NOTIFICATIONS ====================

@api_router.get("/contractor-notifications")
async def get_contractor_notifications(contractor: dict = Depends(get_current_contractor)):
    """Get notifications for the current contractor"""
    notifications = await db.notifications.find(
        {"contractor_id": contractor["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Mark unread count
    unread_count = len([n for n in notifications if not n.get("is_read")])
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@api_router.post("/contractor-notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, contractor: dict = Depends(get_current_contractor)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notification_id, "contractor_id": contractor["id"]},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Уведомление отмечено как прочитанное"}

@api_router.get("/contractor-deals")
async def get_contractor_deals(contractor: dict = Depends(get_current_contractor)):
    """Get deals where contractor is assigned to any stage"""
    # Find all deals where this contractor is assigned
    deals = []
    async for deal in db.deals.find({}, {"_id": 0}):
        # Check if contractor is assigned to any stage
        stages = deal.get("stages", {})
        for stage_key, stage_data in stages.items():
            if stage_data.get("contractor_id") == contractor["id"]:
                deals.append(deal)
                break
        # Also check main contractor
        if deal.get("contractor_id") == contractor["id"]:
            if deal not in deals:
                deals.append(deal)
    
    return deals

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

# ==================== BITRIX24 ADMIN ENDPOINTS ====================

@api_router.get("/admin/bitrix24/status")
async def bitrix24_status(current_user: dict = Depends(require_role(["admin"]))):
    """Check Bitrix24 connection status"""
    b24 = get_bitrix24()
    if not b24:
        return {"connected": False, "error": "Bitrix24 not configured"}
    
    result = await b24.test_connection()
    return {
        "connected": result["success"],
        "error": result.get("error") if not result["success"] else None,
        "webhook_url": BITRIX24_WEBHOOK_URL[:50] + "..." if BITRIX24_WEBHOOK_URL else None
    }

@api_router.post("/admin/bitrix24/sync-user/{user_id}")
async def sync_user_to_bitrix24(user_id: str, current_user: dict = Depends(require_role(["admin"]))):
    """Manually sync user to Bitrix24 as contact"""
    b24 = get_bitrix24()
    if not b24:
        raise HTTPException(status_code=503, detail="Bitrix24 not configured")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await b24.create_contact(
        name=user.get("name", ""),
        email=user.get("email", ""),
        phone=user.get("phone"),
        user_type=user.get("user_type", "individual"),
        user_id=user_id
    )
    
    return result

@api_router.post("/admin/bitrix24/create-deal")
async def create_bitrix24_deal(data: dict, current_user: dict = Depends(require_role(["admin"]))):
    """Manually create deal in Bitrix24"""
    b24 = get_bitrix24()
    if not b24:
        raise HTTPException(status_code=503, detail="Bitrix24 not configured")
    
    result = await b24.create_deal(
        title=data.get("title", "Новая сделка"),
        contact_email=data.get("email"),
        car_brand=data.get("brand"),
        car_model=data.get("model"),
        price_usd=data.get("price"),
        stage=data.get("stage", "NEW"),
        comments=data.get("comments")
    )
    
    return result

@api_router.post("/admin/bitrix24/create-task")
async def create_bitrix24_task(data: dict, current_user: dict = Depends(require_role(["admin"]))):
    """Manually create task in Bitrix24"""
    b24 = get_bitrix24()
    if not b24:
        raise HTTPException(status_code=503, detail="Bitrix24 not configured")
    
    result = await b24.create_task(
        title=data.get("title", "Новая задача"),
        description=data.get("description", ""),
        responsible_id=data.get("responsible_id", 1),
        deadline_days=data.get("deadline_days", 3),
        priority=data.get("priority", 1)
    )
    
    return result

@api_router.get("/admin/bitrix24/users")
async def get_bitrix24_users(current_user: dict = Depends(require_role(["admin"]))):
    """Get Bitrix24 users list"""
    b24 = get_bitrix24()
    if not b24:
        raise HTTPException(status_code=503, detail="Bitrix24 not configured")
    
    result = await b24.get_user_list()
    return result

# Include router and configure app
# ==================== TELEGRAM INTEGRATION ====================

import random
import string

# Store pending telegram verifications (in production, use Redis or DB)
telegram_pending_verifications = {}

# Store pending message context for two-way messaging
# Format: {chat_id: {"deal_id": ..., "stage_key": ..., "user_id": ..., "user_type": ...}}
telegram_message_context = {}


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
        # Get user's deals with assigned contractors
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
        # Get contractor's assigned stages
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
    content: str
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by_client": sender_type == "client",
        "read_by_contractor": sender_type == "contractor",
        "source": "telegram"
    }
    await db.deal_messages.insert_one(message_doc)
    return message_doc


@api_router.post("/telegram/webhook")
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
            
            # Parse callback data
            parts = callback_data.split(":")
            action = parts[0] if parts else ""
            
            if action == "reply" and len(parts) >= 3:
                # User clicked "Reply" button
                deal_id = parts[1]
                stage_key = parts[2]
                
                # Find user by chat_id
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
                
                # Get deal info for confirmation
                deal = await db.deals.find_one({"id": deal_id})
                car_name = ""
                if deal:
                    car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
                
                # Store context for next message
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
                # User selected a chat from the list
                deal_id = parts[1]
                stage_key = parts[2]
                
                # Find user by chat_id
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
                
                # Get deal info
                deal = await db.deals.find_one({"id": deal_id})
                car_name = ""
                if deal:
                    car_name = deal.get("car_info", {}).get("brand", "") + " " + deal.get("car_info", {}).get("model", "")
                
                # Store context
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
            text = message.get("text", "")
            username = message.get("from", {}).get("username")
            first_name = message.get("from", {}).get("first_name", "")
            
            # Handle commands
            if text.startswith("/start"):
                # Check if there's a deep link parameter
                parts = text.split(" ")
                if len(parts) > 1:
                    verification_code = parts[1]
                    # Try to verify user
                    if verification_code in telegram_pending_verifications:
                        user_id = telegram_pending_verifications[verification_code]["user_id"]
                        user_type = telegram_pending_verifications[verification_code]["type"]
                        
                        # Update user's telegram_chat_id
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
                        
                        # Remove from pending
                        del telegram_pending_verifications[verification_code]
                        
                        # Send welcome message
                        await telegram_service.send_welcome_message(chat_id, user_name)
                        return {"ok": True}
                
                # AUTO-LINK: Try to find user/contractor by Telegram username
                auto_linked = False
                if username:
                    # Normalize username (remove @ if present)
                    normalized_username = username.lstrip('@').lower()
                    
                    # Check if already linked
                    existing_user = await db.users.find_one({"telegram_chat_id": chat_id})
                    existing_contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                    
                    if not existing_user and not existing_contractor:
                        # Try to find user by telegram username
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
                            # Try to find contractor by telegram username
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
                        # Already linked
                        auto_linked = True
                        user_name = existing_user.get("name") if existing_user else existing_contractor.get("company_name", first_name)
                        await telegram_service.send_telegram_message(
                            chat_id,
                            f"👋 С возвращением, {user_name}!\n\n"
                            "Ваш Telegram уже привязан к аккаунту.\n\n"
                            "<b>Команды:</b>\n"
                            "/chats - Показать активные чаты\n"
                            "/help - Справка"
                        )
                
                if not auto_linked:
                    # Regular /start - show instructions
                    await telegram_service.send_telegram_message(
                        chat_id,
                        f"👋 Привет, {first_name}!\n\n"
                        "Для получения уведомлений привяжите Telegram в личном кабинете на сайте:\n"
                        "Настройки → Привязать Telegram\n\n"
                        "<b>Команды:</b>\n"
                        "/chats - Показать активные чаты\n"
                        "/help - Справка"
                    )
            
            elif text.startswith("/help"):
                await telegram_service.send_telegram_message(
                    chat_id,
                    "📋 <b>Команды бота:</b>\n\n"
                    "/start - Начать работу с ботом\n"
                    "/chats - Показать активные чаты\n"
                    "/cancel - Отменить выбор чата\n"
                    "/help - Показать справку\n\n"
                    "Вы можете отвечать на уведомления о сообщениях прямо в Telegram."
                )
            
            elif text.startswith("/chats"):
                # Show list of active chats
                user = await db.users.find_one({"telegram_chat_id": chat_id})
                contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                
                if user:
                    active_chats = await get_user_active_chats(user["id"], "user")
                elif contractor:
                    active_chats = await get_user_active_chats(contractor["id"], "contractor")
                else:
                    await telegram_service.send_telegram_message(
                        chat_id,
                        "❌ Ваш Telegram не привязан к аккаунту.\n\n"
                        "Привяжите Telegram в личном кабинете на сайте."
                    )
                    return {"ok": True}
                
                if active_chats:
                    await telegram_service.send_chat_selection(chat_id, active_chats)
                else:
                    await telegram_service.send_no_active_chats(chat_id)
            
            elif text.startswith("/cancel"):
                # Clear context
                if chat_id in telegram_message_context:
                    del telegram_message_context[chat_id]
                await telegram_service.send_telegram_message(
                    chat_id,
                    "✖️ Выбор чата отменён.\n\nИспользуйте /chats для выбора чата."
                )
            
            elif not text.startswith("/"):
                # Regular message - check if we have context
                if chat_id in telegram_message_context:
                    ctx = telegram_message_context[chat_id]
                    
                    # Send message to deal chat
                    await send_message_to_deal_chat(
                        deal_id=ctx["deal_id"],
                        stage_key=ctx["stage_key"],
                        sender_id=ctx["user_id"],
                        sender_type="client" if ctx["user_type"] == "user" else "contractor",
                        sender_name=ctx["user_name"],
                        content=text
                    )
                    
                    # Send confirmation
                    await telegram_service.send_message_confirmation(
                        chat_id,
                        ctx["car_name"],
                        ctx["stage_key"]
                    )
                    
                    # Notify the other party
                    deal = await db.deals.find_one({"id": ctx["deal_id"]})
                    if deal and ctx["user_type"] == "user":
                        # User sent message, notify contractor
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
                        # Contractor sent message, notify user
                        client_id = deal.get("user_id")
                        if client_id:
                            client = await db.users.find_one({"id": client_id})
                            if client and client.get("telegram_chat_id"):
                                await telegram_service.notify_new_message(
                                    client["telegram_chat_id"],
                                    ctx["user_name"],
                                    ctx["car_name"],
                                    telegram_service.STAGE_LABELS.get(ctx["stage_key"], ctx["stage_key"]),
                                    text,
                                    ctx["deal_id"],
                                    ctx["stage_key"]
                                )
                    
                    # Keep context for continuous conversation
                    # Clear only if user explicitly uses /cancel
                    
                else:
                    # No context - show chat selection
                    user = await db.users.find_one({"telegram_chat_id": chat_id})
                    contractor = await db.contractors.find_one({"telegram_chat_id": chat_id})
                    
                    if user:
                        active_chats = await get_user_active_chats(user["id"], "user")
                    elif contractor:
                        active_chats = await get_user_active_chats(contractor["id"], "contractor")
                    else:
                        await telegram_service.send_telegram_message(
                            chat_id,
                            "❌ Ваш Telegram не привязан к аккаунту.\n\n"
                            "Привяжите Telegram в личном кабинете на сайте."
                        )
                        return {"ok": True}
                    
                    if active_chats:
                        if len(active_chats) == 1:
                            # Auto-select single chat
                            chat = active_chats[0]
                            user_id = user["id"] if user else contractor["id"]
                            user_type = "user" if user else "contractor"
                            user_name = user.get("name", "Клиент") if user else contractor.get("company_name", "Подрядчик")
                            
                            telegram_message_context[chat_id] = {
                                "deal_id": chat["deal_id"],
                                "stage_key": chat["stage_key"],
                                "user_id": user_id,
                                "user_type": user_type,
                                "user_name": user_name,
                                "car_name": chat["car_name"]
                            }
                            
                            # Send message directly
                            await send_message_to_deal_chat(
                                deal_id=chat["deal_id"],
                                stage_key=chat["stage_key"],
                                sender_id=user_id,
                                sender_type="client" if user_type == "user" else "contractor",
                                sender_name=user_name,
                                content=text
                            )
                            
                            await telegram_service.send_message_confirmation(
                                chat_id,
                                chat["car_name"],
                                chat["stage_key"]
                            )
                        else:
                            # Multiple chats - ask user to select
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

@api_router.post("/telegram/link")
async def link_telegram(current_user: dict = Depends(get_current_user)):
    """Generate link for user to connect their Telegram"""
    # Generate verification code
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Store pending verification
    telegram_pending_verifications[code] = {
        "user_id": current_user["id"],
        "type": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Get bot username
    bot_info = await telegram_service.get_bot_info()
    bot_username = bot_info.get("result", {}).get("username", "your_bot")
    
    return {
        "link": f"https://t.me/{bot_username}?start={code}",
        "code": code,
        "bot_username": bot_username
    }

@api_router.post("/contractor/telegram/link")
async def link_contractor_telegram(current_user: dict = Depends(get_current_contractor)):
    """Generate link for contractor to connect their Telegram"""
    # Generate verification code
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Store pending verification
    telegram_pending_verifications[code] = {
        "user_id": current_user["id"],
        "type": "contractor",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Get bot username
    bot_info = await telegram_service.get_bot_info()
    bot_username = bot_info.get("result", {}).get("username", "your_bot")
    
    return {
        "link": f"https://t.me/{bot_username}?start={code}",
        "code": code,
        "bot_username": bot_username
    }

@api_router.get("/telegram/status")
async def get_telegram_status(current_user: dict = Depends(get_current_user)):
    """Check if user has linked Telegram"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "telegram_chat_id": 1, "telegram_username": 1})
    return {
        "linked": bool(user.get("telegram_chat_id")),
        "username": user.get("telegram_username")
    }

@api_router.post("/telegram/unlink")
async def unlink_telegram(current_user: dict = Depends(get_current_user)):
    """Unlink Telegram from user account"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$unset": {"telegram_chat_id": "", "telegram_username": ""}}
    )
    return {"message": "Telegram отвязан"}

@api_router.post("/telegram/test")
async def test_telegram_notification(current_user: dict = Depends(get_current_user)):
    """Send test notification to user's Telegram"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "telegram_chat_id": 1, "name": 1})
    
    if not user.get("telegram_chat_id"):
        raise HTTPException(status_code=400, detail="Telegram не привязан")
    
    success = await telegram_service.send_telegram_message(
        user["telegram_chat_id"],
        f"🔔 <b>Тестовое уведомление</b>\n\nПривет, {user.get('name', 'пользователь')}! Уведомления работают корректно."
    )
    
    if success:
        return {"message": "Тестовое уведомление отправлено"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомления")

@api_router.get("/admin/telegram/stats")
async def get_telegram_stats(current_user: dict = Depends(require_role(["admin"]))):
    """Get statistics about Telegram connections"""
    # Count users
    total_users = await db.users.count_documents({})
    linked_users = await db.users.count_documents({"telegram_chat_id": {"$exists": True, "$ne": None}})
    users_with_telegram_field = await db.users.count_documents({"telegram": {"$exists": True, "$ne": None, "$ne": ""}})
    
    # Count contractors
    total_contractors = await db.contractors.count_documents({})
    linked_contractors = await db.contractors.count_documents({"telegram_chat_id": {"$exists": True, "$ne": None}})
    contractors_with_telegram_field = await db.contractors.count_documents({"telegram": {"$exists": True, "$ne": None, "$ne": ""}})
    
    # Get users with telegram username but not linked
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

@api_router.post("/admin/telegram/send-invites")
async def send_telegram_invites(current_user: dict = Depends(require_role(["admin"]))):
    """Send invitation messages to all linked Telegram users to verify their accounts are working"""
    results = {"users_notified": 0, "contractors_notified": 0, "errors": []}
    
    # Get all linked users
    linked_users = await db.users.find(
        {"telegram_chat_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "telegram_chat_id": 1, "name": 1}
    ).to_list(500)
    
    for user in linked_users:
        try:
            success = await telegram_service.send_telegram_message(
                user["telegram_chat_id"],
                f"👋 Привет, {user.get('name', 'пользователь')}!\n\n"
                "Это напоминание о том, что ваш Telegram подключен к CarBridge.\n"
                "Вы будете получать уведомления о сделках и сообщениях.\n\n"
                "/chats - Показать активные чаты"
            )
            if success:
                results["users_notified"] += 1
        except Exception as e:
            results["errors"].append(f"User {user.get('name')}: {str(e)}")
    
    # Get all linked contractors
    linked_contractors = await db.contractors.find(
        {"telegram_chat_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "telegram_chat_id": 1, "company_name": 1}
    ).to_list(500)
    
    for contractor in linked_contractors:
        try:
            success = await telegram_service.send_telegram_message(
                contractor["telegram_chat_id"],
                f"👋 Привет, {contractor.get('company_name', 'подрядчик')}!\n\n"
                "Это напоминание о том, что ваш Telegram подключен к CarBridge.\n"
                "Вы будете получать уведомления о тендерах и сообщениях клиентов.\n\n"
                "/chats - Показать активные чаты"
            )
            if success:
                results["contractors_notified"] += 1
        except Exception as e:
            results["errors"].append(f"Contractor {contractor.get('company_name')}: {str(e)}")
    
    return results

# ==================== END TELEGRAM INTEGRATION ====================

app.include_router(api_router)

# Include modular routers (new refactored routes)
app.include_router(catalog_routes.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Bitrix24 integration
BITRIX24_WEBHOOK_URL = os.environ.get("BITRIX24_WEBHOOK_URL")
if BITRIX24_WEBHOOK_URL:
    bitrix24 = init_bitrix24(BITRIX24_WEBHOOK_URL)
    logger.info(f"Bitrix24 integration initialized")
else:
    bitrix24 = None
    logger.warning("Bitrix24 webhook URL not configured")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
