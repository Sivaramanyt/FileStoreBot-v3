import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8244813008:AAF9Ad2f4yy99wXXsGH7CSRCfhXvGOlx8dU")
    API_ID = int(os.getenv("API_ID", "29542645"))
    API_HASH = os.getenv("API_HASH", "06e505b8418565356ae79365df5d69e0")
    OWNER_ID = int(os.getenv("OWNER_ID", "1206988513"))
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://Sivaraman444:Rama9789@cluster0.8lxln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME = os.getenv("DB_NAME", "cluster0")
    FORCE_SUB_CHANNELS = os.getenv("FORCE_SUB_CHANNELS", "-1002429072244").split(",")
    PREMIUM_QR_URL = os.getenv("PREMIUM_QR_URL", "https://envs.sh/in5.jpg")
    PREMIUM_UPI_ID = os.getenv("PREMIUM_UPI_ID", "sivaramanc49@okaxis")
    SHORTLINK_URL = os.getenv("SHORTLINK_URL", "https://arolinks.com")
    SHORTLINK_API = os.getenv("SHORTLINK_API", "139ebf8c6591acc6a69db83f200f2285874dbdbf")
    
    # Bot settings
    FREE_LIMIT = 3  # Free videos limit
    PREMIUM_PRICE = 50  # Premium price in rupees
    VERIFICATION_VALIDITY_HOURS = 6  # Verification token validity (6 hours)
