"""Catalog routes for car search and browsing"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import urllib.parse
import logging

import sys
sys.path.insert(0, '/app/backend')

from database import db
from utils.auth import get_current_user
from utils.cache import get_cached, set_cache
from services.che168 import Che168API
from services.calculator import calculate_customs_price, CalculatorInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["catalog"])


# ==================== MODELS ====================

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


class CalculatorInput(BaseModel):
    price_cny: float
    age: str  # "under3", "3to5", "over5"
    engine_type: str
    engine_volume: Optional[int] = None
    user_type: str = "individual"
    use_decree_140: bool = False
    payment_via_platform: bool = True


# ==================== STATIC CATALOG DATA ====================

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
        "features": ["EREV гибрид", "1100 км запас хода", "5 мест", "AD Pro автопилот"],
        "popularity": 91
    },
    # NIO
    {
        "id": "nio-es6",
        "brand": "NIO", "brand_cn": "蔚来",
        "model": "ES6", "model_cn": "ES6",
        "year_from": 2019, "year_to": 2024,
        "price_from_cny": 358000, "price_to_cny": 428000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Премиальный электрический SUV с возможностью замены батареи.",
        "features": ["Battery Swap", "NOMI AI", "510 км запас хода", "NIO Pilot"],
        "popularity": 89
    },
    {
        "id": "nio-et5",
        "brand": "NIO", "brand_cn": "蔚来",
        "model": "ET5", "model_cn": "ET5",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 298000, "price_to_cny": 378000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Спортивный электроседан. Конкурент BMW 3 серии.",
        "features": ["Battery Swap", "1000 км с батареей 150kWh", "0-100 за 4.3с", "AR/VR"],
        "popularity": 87
    },
    # Zeekr
    {
        "id": "zeekr-001",
        "brand": "Zeekr", "brand_cn": "极氪",
        "model": "001", "model_cn": "001",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 299000, "price_to_cny": 389000,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "wagon",
        "image_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800",
        "description": "Премиальный электрический шутинг-брейк от Geely.",
        "features": ["SEA платформа", "732 км запас хода", "0-100 за 3.8с", "Frameless doors"],
        "popularity": 86
    },
    # XPeng
    {
        "id": "xpeng-p7",
        "brand": "XPeng", "brand_cn": "小鹏",
        "model": "P7", "model_cn": "P7",
        "year_from": 2020, "year_to": 2024,
        "price_from_cny": 219900, "price_to_cny": 339900,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Умный электроседан с продвинутым автопилотом XPILOT.",
        "features": ["XPILOT 4.0", "706 км запас хода", "XGPT голосовой помощник", "OTA обновления"],
        "popularity": 85
    },
    {
        "id": "xpeng-g9",
        "brand": "XPeng", "brand_cn": "小鹏",
        "model": "G9", "model_cn": "G9",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 309900, "price_to_cny": 469900,
        "engine_type": "electric", "engine_volume": None,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Флагманский электрический SUV с быстрой зарядкой 800V.",
        "features": ["800V архитектура", "702 км запас хода", "XPILOT 4.0", "5 мин = 200 км"],
        "popularity": 84
    },
    # Geely
    {
        "id": "geely-monjaro",
        "brand": "Geely", "brand_cn": "吉利",
        "model": "Monjaro", "model_cn": "星越L",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 139700, "price_to_cny": 189700,
        "engine_type": "ice", "engine_volume": 2000,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Премиальный SUV от Geely на платформе CMA.",
        "features": ["CMA платформа", "2.0T 238 л.с.", "7DCT", "Премиум интерьер"],
        "popularity": 83
    },
    # Changan
    {
        "id": "changan-uni-v",
        "brand": "Changan", "brand_cn": "长安",
        "model": "UNI-V", "model_cn": "UNI-V",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 109900, "price_to_cny": 149900,
        "engine_type": "ice", "engine_volume": 1500,
        "body_type": "sedan",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800",
        "description": "Спортивный лифтбек с агрессивным дизайном.",
        "features": ["Blue Whale 1.5T", "188 л.с.", "7DCT", "Спортивный дизайн"],
        "popularity": 82
    },
    # Haval
    {
        "id": "haval-jolion",
        "brand": "Haval", "brand_cn": "哈弗",
        "model": "Jolion", "model_cn": "初恋",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 98900, "price_to_cny": 128900,
        "engine_type": "ice", "engine_volume": 1500,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Компактный городской кроссовер. Отличное соотношение цена/качество.",
        "features": ["1.5T 150 л.с.", "7DCT", "Полный привод опционально", "Экономичный"],
        "popularity": 81
    },
    # Tank
    {
        "id": "tank-300",
        "brand": "Tank", "brand_cn": "坦克",
        "model": "300", "model_cn": "300",
        "year_from": 2021, "year_to": 2024,
        "price_from_cny": 199800, "price_to_cny": 289800,
        "engine_type": "ice", "engine_volume": 2000,
        "body_type": "suv",
        "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
        "description": "Ретро-внедорожник с современными технологиями.",
        "features": ["2.0T 227 л.с.", "Полный привод", "Блокировки", "Ретро дизайн"],
        "popularity": 88
    },
    {
        "id": "tank-500",
        "brand": "Tank", "brand_cn": "坦克",
        "model": "500", "model_cn": "500",
        "year_from": 2022, "year_to": 2024,
        "price_from_cny": 339800, "price_to_cny": 399800,
        "engine_type": "hybrid", "engine_volume": 2000,
        "body_type": "suv",
        "image_url": "https://images.pexels.com/photos/32912506/pexels-photo-32912506.jpeg?w=800",
        "description": "Премиальный полноразмерный внедорожник.",
        "features": ["3.0T V6 354 л.с.", "Пневмоподвеска", "Полный привод", "Люкс интерьер"],
        "popularity": 86
    },
]


# ==================== HELPER FUNCTIONS ====================

def generate_search_links(brand: str = None, model: str = None, query: str = None):
    """Generate search URLs for Chinese car platforms"""
    search_term = query or f"{brand or ''} {model or ''}".strip()
    encoded = urllib.parse.quote(search_term)
    
    return {
        "che168": f"https://www.che168.com/china/a0_0msdgscncgpi1ltocsp1exx0/?keyword={encoded}",
        "58": f"https://m.58.com/ershouche/?keyword={encoded}",
        "guazi": f"https://www.guazi.com/buy/?search={encoded}",
        "dongchedi": f"https://www.dongchedi.com/search?keyword={encoded}",
    }


# ==================== ENDPOINTS ====================

@router.get("/brands")
async def get_catalog_brands():
    """Get list of all brands in catalog - fetches live data from Che168 API"""
    try:
        che168_brands = await Che168API.get_brands()
        if che168_brands:
            return che168_brands
    except Exception as e:
        logger.error(f"Error fetching Che168 brands: {e}")
    
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


@router.get("/models/{brand_slug}")
async def get_catalog_models(brand_slug: str):
    """Get list of all models for a specific brand"""
    try:
        models = await Che168API.get_models(brand_slug)
        if models:
            return models
    except Exception as e:
        logger.error(f"Error fetching models from Che168 for {brand_slug}: {e}")
    
    return []


@router.get("/search", response_model=CatalogSearchResult)
async def search_catalog(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    mileage_from: Optional[int] = None,
    mileage_to: Optional[int] = None,
    engine_type: Optional[str] = None,
    body_type: Optional[str] = None,
    query: Optional[str] = None,
    exclude_brands: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Search cars in catalog with filters - fetches live data from Che168 API"""
    
    # Parse excluded brands
    excluded_brands_list = []
    if exclude_brands:
        excluded_brands_list = [b.strip().lower() for b in exclude_brands.split(',') if b.strip()]
    
    # Support both parameter naming conventions
    actual_min_price = min_price or price_from
    actual_max_price = max_price or price_to
    actual_min_year = min_year or year_from
    actual_max_year = max_year or year_to
    
    # Try Che168 API first
    try:
        che168_result = await Che168API.search_cars(
            mark=brand,
            model=model,
            year_from=actual_min_year,
            year_to=actual_max_year,
            price_from=actual_min_price,
            price_to=actual_max_price,
            engine_type=engine_type,
            body_type=body_type,
            page=page,
            per_page=limit
        )
        
        if che168_result["cars"]:
            cars = che168_result["cars"]
            
            # Apply excluded brands filter
            if excluded_brands_list:
                cars = [c for c in cars if c["brand"].lower() not in excluded_brands_list]
            
            # Apply query filter
            if query:
                query_lower = query.lower()
                cars = [c for c in cars if 
                    query_lower in c["brand"].lower() or 
                    query_lower in c["model"].lower() or
                    query_lower in c.get("description", "").lower()
                ]
            
            # Apply mileage filter
            if mileage_from is not None or mileage_to is not None:
                filtered_cars = []
                for c in cars:
                    car_mileage = c.get("mileage", 0) or 0
                    if mileage_from and car_mileage < mileage_from:
                        continue
                    if mileage_to and car_mileage > mileage_to:
                        continue
                    filtered_cars.append(c)
                cars = filtered_cars
            
            search_links = generate_search_links(brand, model, query)
            
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
    
    # Fallback to static data
    filtered = CHINESE_CAR_CATALOG.copy()
    
    if brand:
        filtered = [c for c in filtered if c["brand"].lower() == brand.lower()]
    if model:
        filtered = [c for c in filtered if model.lower() in c["model"].lower()]
    if actual_min_price:
        filtered = [c for c in filtered if c["price_from_cny"] >= actual_min_price]
    if actual_max_price:
        filtered = [c for c in filtered if c["price_from_cny"] <= actual_max_price]
    if actual_min_year:
        filtered = [c for c in filtered if c["year_to"] is None or c["year_to"] >= actual_min_year]
    if actual_max_year:
        filtered = [c for c in filtered if c["year_from"] <= actual_max_year]
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
    
    filtered.sort(key=lambda x: x["popularity"], reverse=True)
    
    total = len(filtered)
    pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated = filtered[start:end]
    
    search_links = generate_search_links(brand, model, query)
    
    return CatalogSearchResult(
        cars=[CatalogCarModel(**c) for c in paginated],
        total=total,
        page=page,
        pages=pages,
        search_links=search_links
    )


@router.get("/{car_id}")
async def get_catalog_car(car_id: str):
    """Get single car details from catalog"""
    # First check static catalog
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            return {
                **car,
                "search_links": generate_search_links(car["brand"], car["model"])
            }
    
    # If it's a Che168 ID, fetch from API
    if car_id.startswith("che168-"):
        inner_id = car_id.replace("che168-", "")
        try:
            car_details = await Che168API.get_offer_details(inner_id)
            if car_details:
                images = car_details.get("images", [])
                if isinstance(images, str):
                    try:
                        import json as json_lib
                        images = json_lib.loads(images)
                    except:
                        images = []
                
                return {
                    "id": car_id,
                    "inner_id": inner_id,
                    "brand": car_details.get("mark", "Unknown"),
                    "model": car_details.get("model", "Unknown"),
                    "year_from": car_details.get("year", 2023),
                    "year_to": car_details.get("year", 2023),
                    "price_from_cny": car_details.get("price", 0),
                    "engine_type": Che168API.map_engine_type(car_details.get("engine_type", "")),
                    "engine_volume": int(float(car_details.get("displacement", 0) or 0) * 1000) or None,
                    "body_type": Che168API.map_body_type(car_details.get("body_type", "")),
                    "image_url": images[0] if images else "",
                    "images": images,
                    "mileage": car_details.get("km_age"),
                    "color": car_details.get("color", ""),
                    "address": car_details.get("address", car_details.get("city", "")),
                    "vin": car_details.get("vin", ""),
                    "power": car_details.get("power", 0),
                    "transmission": car_details.get("transmission_type", ""),
                    "drive_type": car_details.get("drive_type", ""),
                    "description": car_details.get("description", ""),
                    "source": "che168",
                    "source_url": car_details.get("url", f"https://www.che168.com/dealer/{inner_id}.html"),
                    "offer_created": car_details.get("offer_created", ""),
                    "first_registration": car_details.get("first_registration", ""),
                    "is_dealer": car_details.get("is_dealer", False),
                    "search_links": generate_search_links(car_details.get("mark", ""), car_details.get("model", ""))
                }
        except Exception as e:
            logger.error(f"Error fetching car details from Che168: {e}")
    
    raise HTTPException(status_code=404, detail="Car not found")


@router.post("/{car_id}/add-to-garage")
async def add_catalog_car_to_garage(
    car_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Add car from catalog to user's garage"""
    catalog_car = None
    
    # Check static catalog
    for car in CHINESE_CAR_CATALOG:
        if car["id"] == car_id:
            catalog_car = car
            break
    
    # If not found and it's a Che168 ID, fetch from API
    if not catalog_car and car_id.startswith("che168-"):
        inner_id = car_id.replace("che168-", "")
        try:
            car_details = await Che168API.get_offer_details(inner_id)
            if car_details:
                # Parse images - can be string or list
                images_raw = car_details.get("images", "")
                if isinstance(images_raw, str):
                    try:
                        import json as json_module
                        images_list = json_module.loads(images_raw) if images_raw else []
                    except:
                        images_list = []
                else:
                    images_list = images_raw if images_raw else []
                
                first_image = images_list[0] if images_list else ""
                
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
                    "image_url": first_image,
                    "source_url": car_details.get("url", ""),
                    "description": car_details.get("description", ""),
                    "body_type": Che168API.map_body_type(car_details.get("body_type", ""))
                }
        except Exception as e:
            logger.error(f"Error fetching car details from Che168: {e}")
    
    if not catalog_car:
        raise HTTPException(status_code=404, detail="Car not found in catalog")
    
    # Create garage entry
    garage_id = str(uuid.uuid4())
    car_year = int(catalog_car.get("year_to") or catalog_car.get("year_from", 2023))
    price_cny = float(catalog_car.get("price_from_cny", 0))
    engine_type = catalog_car.get("engine_type", "ice")
    engine_volume = int(catalog_car.get("engine_volume") or 2000)
    
    # Calculate Belarus price
    calculated_price_usd = None
    calculated_price_byn = None
    
    try:
        current_year = datetime.now().year
        car_age = current_year - car_year
        age_category = "under3" if car_age < 3 else ("3to5" if car_age < 5 else "over5")
        
        calc_input = CalculatorInput(
            price_cny=price_cny,
            age=age_category,
            engine_type=engine_type,
            engine_volume=engine_volume if engine_type != "electric" else 0,
            user_type="individual",
            use_decree_140=False,
            payment_via_platform=True
        )
        calc_result = await calculate_customs_price(calc_input)
        calculated_price_usd = calc_result.total_usd
        calculated_price_byn = calc_result.total_byn
        logger.info(f"Calculated price for {catalog_car['brand']} {catalog_car['model']}: ${calculated_price_usd} / {calculated_price_byn} BYN")
    except Exception as e:
        logger.error(f"Price calculation error: {e}")
    
    garage_doc = {
        "id": garage_id,
        "user_id": current_user["id"],
        "brand": catalog_car["brand"],
        "model": catalog_car["model"],
        "year": car_year,
        "price_cny": price_cny,
        "engine_type": engine_type,
        "engine_volume": engine_volume,
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.garage.insert_one(garage_doc)
    
    return {
        "message": "Car added to garage", 
        "garage_id": garage_id,
        "calculated_price_usd": calculated_price_usd,
        "calculated_price_byn": calculated_price_byn
    }
