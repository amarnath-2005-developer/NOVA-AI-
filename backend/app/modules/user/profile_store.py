import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class ProfileStore:
    """
    Handles raw MongoDB operations for user profiles.
    """
    def __init__(self):
        ca = certifi.where()
        self.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.client[os.getenv("DATABASE_NAME", "nova_ai")]
        self.collection = self.db["users"]

    async def get_user(self, user_id: str) -> dict | None:
        """Fetch a user profile by user_id."""
        return await self.collection.find_one({"user_id": user_id})

    async def upsert_user(self, user_data: dict) -> bool:
        """Create or update a user profile."""
        result = await self.collection.update_one(
            {"user_id": user_data["user_id"]},
            {"$set": user_data},
            upsert=True
        )
        return result.acknowledged

    async def update_field(self, user_id: str, field: str, value: any) -> bool:
        """Update a specific field in the user profile."""
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {field: value}}
        )
        return result.modified_count > 0

    async def push_to_list(self, user_id: str, field: str, value: any) -> bool:
        """Append an item to a list field (like history)."""
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$push": {field: value}}
        )
        return result.modified_count > 0
