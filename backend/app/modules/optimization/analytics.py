"""
NOVA AI — Behavioral Execution Analytics & Telemetry Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements Phase 1 & 6 behavioral telemetry tracking, rolling reliability trends,
agent coordination overhead metrics, and Mongo-persisted execution heatmaps.
"""

import os
import certifi
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("nova.optimization.analytics")


class BehavioralAnalyticsEngine:
    """
    Engine responsible for tracking execution telemetry, mapping success rates,
    rolling tool reliability trends, and generating MongoDB-backed execution heatmaps.
    """

    def __init__(self):
        ca = certifi.where()
        self.db_client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.db_client[os.getenv("DATABASE_NAME", "nova_ai")]
        self.telemetry_col = self.db["agent_behavioral_telemetry"]
        self.heatmap_col = self.db["agent_execution_heatmaps"]

    async def record_execution_telemetry(self, workflow_id: str, tool_name: str,
                                         duration_ms: float, success: bool,
                                         retries: int = 0, recovery_attempted: bool = False,
                                         recovery_successful: bool = False,
                                         coordination_overhead_ms: float = 0.0):
        """Persists granular step execution telemetry to MongoDB for behavioral analysis."""
        telemetry_doc = {
            "workflow_id": workflow_id,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "retries": retries,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "coordination_overhead_ms": coordination_overhead_ms,
            "timestamp": datetime.now()
        }
        
        try:
            await self.telemetry_col.insert_one(telemetry_doc)
            logger.debug(f"Behavioral Telemetry: Recorded execution for '{tool_name}' (success={success})")
            
            # Dynamically update the execution heatmaps collection
            await self._update_execution_heatmap(tool_name, success, duration_ms, retries, recovery_attempted)
        except Exception as e:
            logger.error(f"Failed to record execution telemetry: {e}")

    async def get_tool_reliability_profile(self, tool_name: str, limit: int = 50) -> Dict[str, Any]:
        """Computes rolling success rates and execution trends for a specific tool."""
        try:
            cursor = self.telemetry_col.find({"tool_name": tool_name}).sort("timestamp", -1).limit(limit)
            history = await cursor.to_list(length=limit)
            
            if not history:
                return {"success_rate": 1.0, "avg_duration_ms": 0.0, "total_runs": 0}
                
            total = len(history)
            successes = sum(1 for doc in history if doc.get("success", False))
            durations = [doc.get("duration_ms", 0.0) for doc in history]
            avg_duration = sum(durations) / total
            
            return {
                "success_rate": round(successes / total, 2),
                "avg_duration_ms": round(avg_duration, 2),
                "total_runs": total
            }
        except Exception as e:
            logger.error(f"Failed to fetch tool reliability profile: {e}")
            return {"success_rate": 1.0, "avg_duration_ms": 0.0, "total_runs": 0}

    async def generate_behavioral_heatmap(self, days: int = 14) -> Dict[str, Any]:
        """
        Aggregates long-term behavioral logs to construct an execution heatmap
        highlighting hotspots, unstable regions, and success frequencies.
        """
        since_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": since_date}}},
            {
                "$group": {
                    "_id": "$tool_name",
                    "total_executions": {"$sum": 1},
                    "successful_executions": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "total_duration_ms": {"$sum": "$duration_ms"},
                    "total_retries": {"$sum": "$retries"},
                    "total_recoveries": {"$sum": {"$cond": ["$recovery_attempted", 1, 0]}},
                    "successful_recoveries": {"$sum": {"$cond": ["$recovery_successful", 1, 0]}}
                }
            }
        ]
        
        try:
            results = await self.telemetry_col.aggregate(pipeline).to_list(length=100)
            
            frequently_used = []
            unstable_platforms = []
            recovery_hotspots = []
            
            for res in results:
                tool = res["_id"]
                total = res["total_executions"]
                success_rate = res["successful_executions"] / total
                avg_dur = res["total_duration_ms"] / total
                
                tool_data = {
                    "tool": tool,
                    "total_runs": total,
                    "success_rate": round(success_rate, 2),
                    "avg_duration_ms": round(avg_dur, 2)
                }
                
                frequently_used.append(tool_data)
                
                # Unstable triggers (success rate < 80%)
                if success_rate < 0.80:
                    unstable_platforms.append(tool_data)
                    
                # Recovery hotspot triggers
                if res["total_recoveries"] > 0:
                    rec_rate = res["successful_recoveries"] / res["total_recoveries"] if res["total_recoveries"] else 0
                    recovery_hotspots.append({
                        "tool": tool,
                        "total_recoveries": res["total_recoveries"],
                        "recovery_success_rate": round(rec_rate, 2)
                    })
            
            # Sort maps
            frequently_used.sort(key=lambda x: x["total_runs"], reverse=True)
            unstable_platforms.sort(key=lambda x: x["success_rate"])
            recovery_hotspots.sort(key=lambda x: x["total_recoveries"], reverse=True)
            
            heatmap = {
                "frequently_used_workflows": frequently_used[:5],
                "unstable_platforms": unstable_platforms[:5],
                "recovery_hotspots": recovery_hotspots[:5],
                "generated_at": datetime.now()
            }
            
            # Cache snapshot in the heatmap collection
            await self.heatmap_col.update_one(
                {"id": "latest_heatmap"},
                {"$set": heatmap},
                upsert=True
            )
            return heatmap
        except Exception as e:
            logger.error(f"Failed to generate behavioral heatmap: {e}")
            return {}

    async def _update_execution_heatmap(self, tool_name: str, success: bool,
                                         duration_ms: float, retries: int,
                                         recovery_attempted: bool):
        """Increments historical counts and tracking variables inside the execution heatmap."""
        try:
            await self.heatmap_col.update_one(
                {"tool_name": tool_name},
                {
                    "$inc": {
                        "execution_count": 1,
                        "success_count": 1 if success else 0,
                        "failure_count": 0 if success else 1,
                        "total_duration_ms": duration_ms,
                        "total_retries": retries,
                        "recovery_count": 1 if recovery_attempted else 0
                    },
                    "$set": {
                        "last_executed": datetime.now()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to update execution heatmap: {e}")
