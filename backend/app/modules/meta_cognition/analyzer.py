"""
NOVA AI — Meta-Cognitive Analyzer & Self-Reflection Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements Phase 1 (Meta-Cognitive Analyzer), Phase 4 (Self-Reflection Engine),
and Phase 8 (Cognitive Health Monitoring) tracking cognitive health metrics.
"""

import os
import certifi
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("nova.metacognition.analyzer")


class MetaCognitiveAnalyzer:
    """
    Cognitive health analyzer providing meta-reasoning, reflective analysis,
    orchestration bottleneck checks, and cognitive degradation prevention.
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
        self.reflection_col = self.db["agent_self_reflections"]
        self.health_col = self.db["agent_cognitive_health"]

    async def analyze_orchestration_efficiency(self) -> Dict[str, Any]:
        """Phase 1: Analyzes planning latency, bus overhead, and coordination efficiency."""
        try:
            # Fetch recent telemetry logs from the past 7 days
            since_date = datetime.now() - timedelta(days=7)
            cursor = self.telemetry_col.find({"timestamp": {"$gte": since_date}})
            logs = await cursor.to_list(length=200)
            
            if not logs:
                return {"overhead_ratio": 0.0, "status": "healthy", "message": "No logs recorded yet"}
                
            total_duration = sum(log.get("duration_ms", 0.0) for log in logs)
            total_overhead = sum(log.get("coordination_overhead_ms", 0.0) for log in logs)
            
            overhead_ratio = total_overhead / total_duration if total_duration else 0.0
            
            status = "healthy"
            if overhead_ratio > 0.35:
                status = "degraded"  # Coordination overhead consumes >35% of workflow times
            elif overhead_ratio > 0.20:
                status = "warning"
                
            return {
                "total_duration_ms": round(total_duration, 2),
                "total_overhead_ms": round(total_overhead, 2),
                "overhead_ratio": round(overhead_ratio, 3),
                "status": status,
                "total_steps_audited": len(logs)
            }
        except Exception as e:
            logger.error(f"Failed to analyze orchestration efficiency: {e}")
            return {"overhead_ratio": 0.0, "status": "error"}

    async def perform_self_reflection(self) -> Dict[str, Any]:
        """
        Phase 4: Self-Reflection Engine.
        Executes critical reviews over recent errors and successes to optimize recovery.
        """
        try:
            # Query recent execution logs to extract successes and failures
            cursor = self.telemetry_col.find().sort("timestamp", -1).limit(100)
            logs = await cursor.to_list(length=100)
            
            failures = [l for l in logs if not l.get("success", False)]
            recoveries = [l for l in logs if l.get("recovery_attempted", False)]
            successful_recoveries = [l for l in recoveries if l.get("recovery_successful", False)]
            
            failure_reasons = {}
            for f in failures:
                tool = f.get("tool_name", "unknown")
                failure_reasons[tool] = failure_reasons.get(tool, 0) + 1
                
            reflection = {
                "timestamp": datetime.now(),
                "total_failures_recorded": len(failures),
                "recovery_success_rate": round(len(successful_recoveries) / len(recoveries), 2) if recoveries else 1.0,
                "primary_failure_hotspots": failure_reasons,
                "insights": []
            }
            
            # Generate actionable optimization insights
            for tool, count in failure_reasons.items():
                if count >= 3:
                    insight = f"Tool '{tool}' represents a cognitive bottleneck with {count} recent failures. Recommend proactive execution timing tuning."
                    reflection["insights"].append(insight)
                    logger.warning(f"Self-Reflection Insight: {insight}")
                    
            if not reflection["insights"]:
                reflection["insights"].append("System cognitive pathways are highly optimized. Success metrics are stable.")
                
            # Persist self-reflection snapshot
            await self.reflection_col.insert_one(reflection)
            return reflection
        except Exception as e:
            logger.error(f"Self-reflection execution failed: {e}")
            return {"insights": ["Self-reflection skipped due to database error."]}

    async def monitor_cognitive_health(self) -> Dict[str, Any]:
        """
        Phase 8: Cognitive Health Monitoring.
        Tracks cognitive dimensions (bottlenecks, overhead ratios, memory growth, conflicts).
        """
        try:
            efficiency = await self.analyze_orchestration_efficiency()
            reflection = await self.perform_self_reflection()
            
            # Calculate memory volumes (rough count of documents)
            mem_count = await self.db["agent_procedural_memory"].count_documents({})
            telemetry_count = await self.db["agent_behavioral_telemetry"].count_documents({})
            
            # Coordination bottlenecks (any tool failing >30% of executions)
            heatmap_cursor = self.db["agent_execution_heatmaps"].find()
            heatmaps = await heatmap_cursor.to_list(length=50)
            
            bottlenecks = []
            for h in heatmaps:
                count = h.get("execution_count", 0)
                fails = h.get("failure_count", 0)
                if count > 3 and (fails / count) > 0.30:
                    bottlenecks.append({
                        "tool_name": h.get("tool_name"),
                        "failure_rate": round(fails / count, 2)
                    })
                    
            health_status = "optimal"
            if len(bottlenecks) >= 2 or efficiency.get("status") == "degraded":
                health_status = "attention_needed"
                
            health_report = {
                "timestamp": datetime.now(),
                "status": health_status,
                "coordination_overhead_ratio": efficiency.get("overhead_ratio", 0.0),
                "memory_metrics": {
                    "procedural_memory_records": mem_count,
                    "behavioral_telemetry_records": telemetry_count
                },
                "cognitive_bottlenecks": bottlenecks,
                "recommended_actions": []
            }
            
            if health_status == "attention_needed":
                health_report["recommended_actions"].append("Trigger dynamic capability compression and reorganize execution paths.")
            else:
                health_report["recommended_actions"].append("No structural reorganization required at this time.")
                
            # Log health metrics in db
            await self.health_col.insert_one(health_report)
            return health_report
        except Exception as e:
            logger.error(f"Failed to monitor cognitive health: {e}")
            return {"status": "error"}
