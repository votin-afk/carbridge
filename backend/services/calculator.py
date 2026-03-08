"""Calculator service for customs duties"""
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
from datetime import datetime, timezone
import httpx
import logging

logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class CalculatorInput(BaseModel):
    price_cny: float
    age: Literal["under3", "3to5", "over5"]
    engine_type: Literal["ice", "hybrid", "electric"]
    engine_volume: Optional[int] = None
    user_type: Literal["individual", "legal"] = "individual"
    use_decree_140: bool = False
    payment_via_platform: bool = True


class CalculatorResult(BaseModel):
    price_cny: float
    price_eur: float
    price_usd: float
    customs_duty: float
    utilization_fee: float
    vat: float
    fixed_costs_byn: float
    fixed_costs_usd: float
    platform_commission: float
    payment_commission: float
    decree_140_discount: float
    total_byn: float
    total_usd: float
    breakdown: dict


# ==================== EXCHANGE RATES ====================

_exchange_rates_cache: Dict[str, Any] = {"rates": None, "updated": None}


async def get_exchange_rates() -> Dict[str, float]:
    """Fetch exchange rates from NBRB API or use cached values"""
    now = datetime.now(timezone.utc)
    
    if _exchange_rates_cache["rates"] and _exchange_rates_cache["updated"]:
        cache_age = (now - _exchange_rates_cache["updated"]).total_seconds()
        if cache_age < 3600:  # Cache for 1 hour
            return _exchange_rates_cache["rates"]
    
    default_rates = {"CNY_EUR": 0.127, "CNY_USD": 0.138, "USD_BYN": 3.25, "EUR_BYN": 3.55}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
                    _exchange_rates_cache["rates"] = {**default_rates, **rates}
                    _exchange_rates_cache["updated"] = now
                    return _exchange_rates_cache["rates"]
    except Exception as e:
        logger.error(f"Failed to fetch exchange rates: {e}")
    
    return default_rates


# ==================== CALCULATOR LOGIC ====================

async def calculate_customs_price(data: CalculatorInput) -> CalculatorResult:
    """Calculate total customs price for importing a car"""
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
        customs_duty, utilization_fee, vat = _calculate_individual_duties(
            data, price_eur
        )
    else:
        customs_duty, utilization_fee, vat = _calculate_legal_duties(
            data, price_eur
        )
    
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
    
    # Комиссия платформы 3% от стоимости авто в USD
    platform_commission_usd = price_usd * 0.03
    platform_commission_byn = platform_commission_usd * rates["USD_BYN"]
    
    # Комиссия за оплату 1.5%
    payment_commission_usd = price_usd * 0.015
    payment_commission_byn = payment_commission_usd * rates["USD_BYN"]
    
    # Применение льготы по Указу 140
    decree_140_discount_byn = 0
    if data.user_type == "individual" and data.use_decree_140:
        discount_on_duty = customs_duty_byn * 0.5
        discount_on_vat = vat_byn * 0.5
        decree_140_discount_byn = discount_on_duty + discount_on_vat
        customs_duty_byn = customs_duty_byn - discount_on_duty
        vat_byn = vat_byn - discount_on_vat
    
    # Final total
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


def _calculate_individual_duties(data: CalculatorInput, price_eur: float) -> tuple:
    """Calculate duties for individuals"""
    customs_duty = 0
    utilization_fee = 0
    vat = 0
    
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
    
    return customs_duty, utilization_fee, vat


def _calculate_legal_duties(data: CalculatorInput, price_eur: float) -> tuple:
    """Calculate duties for legal entities"""
    customs_duty = 0
    utilization_fee = 0
    vat = 0
    volume = data.engine_volume or 2000
    
    if data.engine_type == "electric":
        customs_duty = 0
        utilization_fee = 1148.86 if data.age == "under3" else 2757.36
    else:
        # Utilization fee based on engine volume
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
        
        # Customs duty
        if data.age == "under3":
            if volume <= 3000:
                customs_duty = price_eur * 0.15
            else:
                duty_by_pct = price_eur * 0.23
                duty_by_volume = volume * 1.57
                customs_duty = max(duty_by_pct, duty_by_volume)
        else:
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
    
    # VAT for legal entities
    if data.engine_type != "electric":
        vat = (price_eur + customs_duty) * 0.20
    
    return customs_duty, utilization_fee, vat
