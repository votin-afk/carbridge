"""Leasing calculator routes"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

import sys
sys.path.insert(0, '/app/backend')

from database import db


router = APIRouter(prefix="/leasing", tags=["leasing"])


# Demo contractors with leasing
DEMO_CONTRACTORS_LEASING = [
    {"id": "leasing-001", "name": "AutoLeasing Pro", "leasing_rate": 8.5},
    {"id": "leasing-002", "name": "China Motors Finance", "leasing_rate": 9.0},
]


class LeasingCalculation(BaseModel):
    car_price_usd: float
    down_payment_percent: float
    term_months: int
    leasing_company_id: Optional[str] = None


@router.post("/calculate")
async def calculate_leasing(data: LeasingCalculation):
    """Calculate leasing payments"""
    rate = 9.0  # Default annual rate
    
    if data.leasing_company_id:
        for c in DEMO_CONTRACTORS_LEASING:
            if c["id"] == data.leasing_company_id and c.get("leasing_rate"):
                rate = c["leasing_rate"]
                break
        
        # Check database contractors
        contractor = await db.contractors.find_one({"id": data.leasing_company_id})
        if contractor and contractor.get("leasing_rate"):
            rate = contractor["leasing_rate"]
    
    down_payment = data.car_price_usd * (data.down_payment_percent / 100)
    financed_amount = data.car_price_usd - down_payment
    
    monthly_rate = rate / 100 / 12
    
    if monthly_rate > 0:
        monthly_payment = financed_amount * (monthly_rate * (1 + monthly_rate)**data.term_months) / ((1 + monthly_rate)**data.term_months - 1)
    else:
        monthly_payment = financed_amount / data.term_months
    
    first_payment = down_payment + monthly_payment
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
