"""Database connection and utilities"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, DB_NAME

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections (for type hints and autocomplete)
users = db.users
contractors = db.contractors
garage = db.garage
deals = db.deals
tenders = db.tenders
applications = db.applications
verifications = db.verifications
accounts = db.accounts
transactions = db.transactions
deal_messages = db.deal_messages
deal_files = db.deal_files
contractor_offers = db.contractor_offers
help_requests = db.help_requests
hot_deals = db.hot_deals
