"""
NOVA AI 2.0 — Workflow Memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stores successful execution plans and learns from past workflows.
The planner queries this before generating new plans.
"""

import os
import certifi
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


class WorkflowMemory:
    """
    Stores and retrieves past execution workflows.
    Successful workflows become templates for the planner.
    Failed workflows inform what to avoid.
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
        self.collection = self.db["agent_workflows"]

    async def store_workflow(self, user_id: str, goal: str, plan: dict,
                            steps_executed: list[dict], success: bool,
                            duration_ms: float) -> bool:
        """Store an execution workflow and its outcome."""
        doc = {
            "user_id": user_id,
            "goal": goal,
            "goal_lower": goal.lower(),  # For text search
            "plan": plan,
            "steps_executed": steps_executed,
            "success": success,
            "duration_ms": duration_ms,
            "created_at": datetime.now(),
            "use_count": 0  # How many times this was referenced
        }
        result = await self.collection.insert_one(doc)
        return result.acknowledged

    async def find_similar_workflows(self, goal: str, user_id: str = None,
                                      limit: int = 3, success_only: bool = True) -> list[dict]:
        """
        Find past workflows similar to the current goal.
        Uses keyword matching on goal text.
        Returns the most recent matching workflows.
        """
        # Extract keywords from the goal
        keywords = [w.lower() for w in goal.split() if len(w) > 2]

        if not keywords:
            return []

        query = {}
        if success_only:
            query["success"] = True
        if user_id:
            query["user_id"] = user_id

        # Match any keyword in the goal
        query["goal_lower"] = {"$regex": "|".join(keywords), "$options": "i"}

        try:
            cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
            results = await cursor.to_list(length=limit)

            # Clean MongoDB ObjectIds for JSON serialization
            for r in results:
                r.pop("_id", None)

            return results
        except Exception:
            return []

    async def increment_use_count(self, goal: str):
        """Increment the use count when a workflow is referenced."""
        try:
            await self.collection.update_one(
                {"goal_lower": goal.lower(), "success": True},
                {"$inc": {"use_count": 1}}
            )
        except Exception:
            pass

    async def get_user_patterns(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get the user's most common successful workflow patterns."""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "success": True}},
                {"$sort": {"use_count": -1, "created_at": -1}},
                {"$limit": limit},
                {"$project": {"_id": 0, "goal": 1, "plan": 1, "use_count": 1}}
            ]
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=limit)
        except Exception:
            return []

    async def cleanup_old_failures(self, days: int = 14):
        """Remove failed workflows older than N days."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        try:
            await self.collection.delete_many({
                "success": False,
                "created_at": {"$lt": cutoff}
            })
        except Exception:
            pass
