import os
import certifi
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class MemoryStore:
    """
    Handles MongoDB operations for the semantic memory layer.
    """
    def __init__(self):
        # Reuse existing database configuration
        ca = certifi.where()
        self.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.client[os.getenv("DATABASE_NAME", "nova_ai")]
        self.collection = self.db["user_memories"]

    async def store_memory(self, user_id: str, text: str, embedding: list[float], metadata: dict = None) -> bool:
        """
        Inserts a new memory document with its vector embedding.
        """
        memory_doc = {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.now()
        }
        result = await self.collection.insert_one(memory_doc)
        return result.acknowledged

    async def get_user_memories(self, user_id: str, limit: int = 1000) -> list[dict]:
        """
        Fetches all memories for a specific user. 
        Limited to 1000 for brute-force performance safety.
        """
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def delete_old_memories(self, user_id: str, days: int = 30) -> int:
        """
        Optional pruning: delete memories older than X days.
        """
        # Logic can be implemented if required by the user
        pass
