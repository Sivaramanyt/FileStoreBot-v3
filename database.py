import motor.motor_asyncio
from config import Config
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URL)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db.users
        self.files = self.db.files
        self.settings = self.db.settings
        self.verifications = self.db.verifications

    async def add_user(self, user_id, username=None, first_name=None):
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "files_accessed": 0,
            "is_premium": False,
            "join_date": datetime.now()
        }
        existing_user = await self.users.find_one({"user_id": user_id})
        if not existing_user:
            await self.users.insert_one(user_data)
            return True
        return False

    async def get_user(self, user_id):
        return await self.users.find_one({"user_id": user_id})

    async def update_user_access(self, user_id):
        await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"files_accessed": 1}}
        )

    async def reset_user_verification(self, user_id):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"files_accessed": 0}}
        )
        # Also clear any existing verification tokens for this user
        await self.verifications.delete_many({"user_id": user_id})

    async def make_premium(self, user_id):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": True}}
        )

    async def store_file(self, file_id, file_name, file_size, file_type, message_id, channel_id=None):
        file_data = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "message_id": message_id,
            "channel_id": channel_id or Config.STORAGE_CHANNEL_ID,
            "uploaded_at": datetime.now()
        }
        result = await self.files.insert_one(file_data)
        return str(result.inserted_id)

    async def get_file(self, file_unique_id):
        try:
            from bson import ObjectId
            return await self.files.find_one({"_id": ObjectId(file_unique_id)})
        except:
            return await self.files.find_one({"file_id": file_unique_id})

    # NEW: Verification token management with 6-hour expiration
    async def create_verification_token(self, user_id, file_id, token):
        """Create a verification token that expires in 6 hours"""
        verification_data = {
            "user_id": user_id,
            "file_id": file_id,
            "token": token,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=6),
            "is_used": False
        }
        await self.verifications.insert_one(verification_data)

    async def verify_token(self, user_id, token):
        """Verify token and check if it's still valid (not expired and not used)"""
        current_time = datetime.now()
        verification = await self.verifications.find_one({
            "user_id": user_id,
            "token": token,
            "is_used": False,
            "expires_at": {"$gt": current_time}
        })
        
        if verification:
            # Mark token as used
            await self.verifications.update_one(
                {"_id": verification["_id"]},
                {"$set": {"is_used": True, "used_at": current_time}}
            )
            return verification["file_id"]
        return None

    async def cleanup_expired_tokens(self):
        """Remove expired verification tokens"""
        current_time = datetime.now()
        await self.verifications.delete_many({
            "expires_at": {"$lt": current_time}
        })

    async def get_total_users(self):
        return await self.users.count_documents({})

    async def get_all_users(self):
        users = []
        async for user in self.users.find({}):
            users.append(user["user_id"])
        return users

    async def update_shortlink(self, url, api_key):
        await self.settings.update_one(
            {"type": "shortlink"},
            {"$set": {"url": url, "api_key": api_key}},
            upsert=True
        )

    async def get_shortlink_settings(self):
        return await self.settings.find_one({"type": "shortlink"})

db = Database()
        
