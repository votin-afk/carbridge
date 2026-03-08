"""Pydantic models for API"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# ==================== AUTH MODELS ====================

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=4)
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: str = "user"
    referrer_code: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ==================== TENDER MODELS ====================

class TenderCreate(BaseModel):
    car_id: str

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

# ==================== CAR APPLICATION MODELS ====================

class CarApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # Section 1: Client Info
    client_type: Optional[str] = "individual"
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    delivery_city: Optional[str] = None
    
    # Section 2: Car Details
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    body_type: Optional[str] = None
    engine_type: Optional[str] = None
    engine_volume: Optional[str] = None
    power_from: Optional[int] = None
    power_to: Optional[int] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    
    # Section 3: Condition
    car_condition: Optional[str] = None
    mileage_max: Optional[str] = None
    allow_damage: Optional[bool] = False
    damage_level: Optional[str] = None
    
    # Section 4: Appearance
    body_color: Optional[str] = None
    exact_color: Optional[str] = None
    color_importance: Optional[str] = None
    interior_color: Optional[str] = None
    interior_material: Optional[str] = None
    
    # Section 5: Options
    options_comfort: Optional[List[str]] = []
    options_electronic: Optional[List[str]] = []
    options_exterior: Optional[List[str]] = []
    options_other: Optional[List[str]] = []
    required_options: Optional[str] = None
    preferred_options: Optional[str] = None
    
    # Section 6: Budget
    budget_china_from: Optional[float] = None
    budget_china_to: Optional[float] = None
    budget_total: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: Optional[str] = "USD"
    budget_min: Optional[float] = None
    payment_method: Optional[str] = None
    
    # Section 7: Timeline & Priorities
    purchase_timeline: Optional[str] = None
    car_purpose: Optional[str] = None
    customs_clearance: Optional[str] = None
    priority_price: Optional[int] = None
    priority_reliability: Optional[int] = None
    priority_technology: Optional[int] = None
    priority_prestige: Optional[int] = None
    priority_fuel: Optional[int] = None
    additional_requirements: Optional[str] = None
    
    # Section 8: Agreement
    agreed_to_terms: Optional[bool] = False
    urgent: Optional[bool] = False
    
    # Link to garage car if from garage
    garage_car_id: Optional[str] = None

# ==================== CONTRACTOR MODELS ====================

class ContractorRegister(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company_name: str
    contact_name: str
    email: EmailStr
    phone: str
    password: str
    services: List[str]
    regions: Optional[List[str]] = []
    description: Optional[str] = None
    license_number: Optional[str] = None
    
    # Service prices
    service_prices: Optional[Dict[str, Any]] = {}
    
    # Leasing specific
    leasing_rate: Optional[float] = None
    leasing_currency: Optional[str] = None

# ==================== DEAL MODELS ====================

class StagePayment(BaseModel):
    deal_id: str
    stage: str
    amount: float
    payment_method: str = "platform"  # platform, external, leasing
    broker_id: Optional[str] = None

# ==================== VERIFICATION MODELS ====================

class VerificationData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    full_name: str
    passport_series: str
    passport_number: str
    passport_issued_by: str
    passport_issue_date: str
    registration_address: str
    birth_date: str
    birth_place: Optional[str] = None
    phone: str
    email: str
