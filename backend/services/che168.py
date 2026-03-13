"""Che168 API service for car catalog"""
import httpx
import logging
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

import sys
sys.path.insert(0, '/app/backend')

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from utils.cache import get_cached, set_cache

logger = logging.getLogger(__name__)

# Che168 API Configuration - from environment
CHE168_API_BASE_URL = os.environ.get("CHE168_API_BASE_URL", "https://api1.auto-api.com/api/v2/che168")
CHE168_API_KEY = os.environ.get("CHE168_API_KEY", "DQugK90Bo5ci1ZeDP6Wr")


class Che168API:
    """API client for Che168 car marketplace"""
    
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
                "count": len(models) * 10,
                "url": f"https://www.che168.com/china/{brand_name.lower()}/"
            })
        
        brands.sort(key=lambda x: x["count"], reverse=True)
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
                engine_map = {
                    "electric": "Электрический (BEV)",
                    "hybrid": "Гибридный (HEV)",
                    "ice": "Бензиновый"
                }
                if engine_type in engine_map:
                    params["engine_type"] = engine_map[engine_type]
            if body_type:
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
                        
                        # Parse images
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
                    
                    next_page = meta.get("next_page")
                    has_more = next_page is not None
                    
                    result_data = {
                        "cars": cars,
                        "total": len(cars) * 100 if has_more else len(cars),
                        "page": page,
                        "pages": page + 10 if has_more else page,
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
    
    @staticmethod
    async def translate_to_russian(text: str) -> str:
        """Translate Chinese text to Russian using LLM"""
        if not text or len(text) < 3:
            return text
        
        # Check if text is mostly Chinese
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars < len(text) * 0.3:
            return text
        
        try:
            from emergentintegrations.llm.chat import chat, UserMessage
            
            response = await chat(
                api_key=None,  # Uses EMERGENT_API_KEY from env
                model="gpt-4o-mini",
                messages=[
                    UserMessage(content=f"Переведи на русский язык (только перевод, без пояснений): {text}")
                ]
            )
            return response.content if response else text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
