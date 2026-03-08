"""Application configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "carbridge-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

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

# Platform fee
PLATFORM_FEE_PERCENT = 3.0
AFFILIATE_COMMISSION_PERCENT = 20.0  # 20% of platform fee goes to referrer
