"""Application configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# JWT
JWT_SECRET = os.environ.get("JWT_SECRET", os.environ.get("JWT_SECRET_KEY", "carbridge_secret_key"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30
JWT_EXPIRATION_HOURS = 24

# MongoDB
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "carbridge")

# API Keys
AUTO_API_KEY = os.environ.get("AUTO_API_KEY", "")
EMERGENT_KEY = os.environ.get("EMERGENT_KEY", "")

# Paths
BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEAL_ADD_FEE = 300  # USD
CONSULTANT_FEE = 200  # $200 for consultant help

# Platform fee
PLATFORM_FEE_PERCENT = 3.0
AFFILIATE_COMMISSION_PERCENT = 20.0  # 20% of platform fee goes to referrer

# Deal constants
PLATFORM_COMMISSION = 0.03  # 3%
PLATFORM_PAYMENT_FEE = 0.01  # +1% if paid through platform
COMMISSION_RATE = 0.03  # 3% platform commission
AFFILIATE_SHARE = 0.20  # 20% of commission goes to affiliate
PARTNER_THRESHOLD = 3  # 3 completed deals to become partner

NEW_DEAL_STAGES = [
    "leasing", "inspection", "export", "logistics_china",
    "insurance", "delivery_rb", "customs", "completion"
]

DEAL_STAGES = ["verification", "contract", "inspection", "payment", "export", "logistics", "delivery"]
