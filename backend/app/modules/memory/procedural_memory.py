"""
NOVA AI 2.0 — Procedural Memory Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evolves NOVA from reactive recovery into adaptive optimization.
Stores and analyzes:
1. Successful generalizable workflows (Procedures)
2. Recovery pattern success rates (Heuristic vs. LLM recovery outcomes)
3. Tool reliability tracking (Success rate per tool)
4. Environment patterns (Site anomalies, UI selector overrides)
"""

import os
import json
import certifi  # type: ignore
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from groq import Groq  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()
# Initialize logger for procedural memory
logger = logging.getLogger("nova.procedural_memory")


class ProceduralMemoryEngine:
    """
    Manages long-term procedural knowledge, enabling compound learning.
    """

    def __init__(self, groq_client: Optional[Groq] = None):
        ca = certifi.where()
        self.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.client[os.getenv("DATABASE_NAME", "nova_ai")]
        
        # MongoDB Collections
        self.coll_procedures = self.db["agent_procedures"]
        self.coll_recovery = self.db["agent_recovery_patterns"]
        self.coll_tools = self.db["agent_tool_reliability"]
        self.coll_env = self.db["agent_environment_patterns"]
        
        self.groq_client = groq_client or Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self._background_tasks = set()

    # ── 1. PROCEDURES (SUCCESSFUL WORKFLOWS) ─────────────────────────────────

    async def record_successful_workflow(self, goal: str, steps: List[dict], duration_ms: float):
        """
        Asynchronously generalizes a successful workflow and records it as a reusable procedure.
        """
        async def _run_generalization():
            try:
                # 1. Ask LLaMA to generalize the goal and the steps
                prompt = f"""You are the Procedural Generalizer for NOVA AI.
Your job is to take a successful system execution path and generalize it into a reusable template.
Replace specific file paths, names, usernames, and search keywords with high-level generic placeholders (like <FILE_PATH>, <QUERY>, <WEBSITE>, <PLATFORM>).

Original Goal: "{goal}"
Steps Executed:
{json.dumps(steps, indent=2)}

Output a valid JSON object matching this structure EXACTLY. Do not add markdown or comments:
{{
  "task_pattern": "generalized task summary (e.g. search for <FILE> and upload to <WEBSITE>)",
  "steps": [
     // Same step structure as inputs, but with generic parameters
  ]
}}"""

                completion = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=800,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(completion.choices[0].message.content.strip())
                pattern = result.get("task_pattern", "").lower()
                gen_steps = result.get("steps", [])
                
                if not pattern or not gen_steps:
                    return

                # 2. Update MongoDB (Upsert procedure template)
                doc = await self.coll_procedures.find_one({"task_pattern": pattern})
                if doc:
                    count = doc.get("success_count", 0) + 1
                    total = doc.get("execution_count", 0) + 1
                    avg_dur = ((doc.get("avg_duration_ms", 0) * doc.get("success_count", 0)) + duration_ms) / count
                    
                    await self.coll_procedures.update_one(
                        {"task_pattern": pattern},
                        {
                            "$set": {
                                "steps": gen_steps,
                                "success_count": count,
                                "execution_count": total,
                                "success_rate": round(count / total, 3),
                                "avg_duration_ms": round(avg_dur, 2),
                                "updated_at": datetime.now()
                            }
                        }
                    )
                else:
                    await self.coll_procedures.insert_one({
                        "task_pattern": pattern,
                        "steps": gen_steps,
                        "success_count": 1,
                        "execution_count": 1,
                        "success_rate": 1.0,
                        "avg_duration_ms": round(duration_ms, 2),
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    })
                
                logger.info(f"Procedural Memory: Generalized & recorded workflow pattern: '{pattern}'")
            except Exception as e:
                logger.error(f"Failed to generalize and record successful workflow: {e}")

        # Run background task safely using strong reference tracking
        task = asyncio.create_task(_run_generalization())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def get_matching_procedure(self, goal: str) -> Optional[dict]:
        """
        Retrieves a highly rated, matching procedural template for a goal.
        """
        try:
            # Query LLaMA briefly to categorize the goal into a pattern
            prompt = f"""You are the Procedural Retriever for NOVA AI.
Given a user's goal, extract its generalized structure (e.g. search <FILE>, launch <APP>, upload <FILE> to <WEBSITE>).

Goal: "{goal}"

Output ONLY a JSON object: {{"pattern": "generalized statement in lower case"}}"""

            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            res = json.loads(completion.choices[0].message.content.strip())
            pattern = res.get("pattern", "").lower()
            
            if not pattern:
                return None

            # Split keywords to do a robust regex match in DB
            keywords = [w.strip() for w in pattern.split() if len(w) > 2]
            if not keywords:
                return None
                
            query = {
                "success_rate": {"$gte": 0.8},
                "task_pattern": {"$regex": "|".join(keywords), "$options": "i"}
            }
            
            doc = await self.coll_procedures.find_one(query, sort=[("success_rate", -1)])
            if doc:
                logger.info(f"Procedural Memory: Retrieved matching template for goal: '{doc['task_pattern']}' (Success rate: {doc['success_rate']})")
                doc.pop("_id", None)
                return doc
        except Exception as e:
            logger.error(f"Failed to query matching procedure: {e}")
        return None

    # ── 2. RECOVERY PATTERNS ──────────────────────────────────────────────────

    async def record_recovery_outcome(self, classification: str, strategy: str, success: bool):
        """Records whether a chosen recovery strategy successfully resolved a category of error."""
        try:
            query = {"classification": classification, "strategy": strategy}
            doc = await self.coll_recovery.find_one(query)
            
            field_to_inc = "success_count" if success else "failure_count"
            
            if doc:
                succ = doc.get("success_count", 0) + (1 if success else 0)
                fail = doc.get("failure_count", 0) + (0 if success else 1)
                total = succ + fail
                
                await self.coll_recovery.update_one(
                    query,
                    {
                        "$inc": {field_to_inc: 1},
                        "$set": {
                            "success_rate": round(succ / total, 3),
                            "updated_at": datetime.now()
                        }
                    }
                )
            else:
                await self.coll_recovery.insert_one({
                    "classification": classification,
                    "strategy": strategy,
                    "success_count": 1 if success else 0,
                    "failure_count": 0 if success else 1,
                    "success_rate": 1.0 if success else 0.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
            logger.info(f"Procedural Memory: Logged recovery strategy outcome: class={classification}, strategy={strategy}, success={success}")
        except Exception as e:
            logger.error(f"Failed to record recovery outcome: {e}")

    async def get_best_recovery_strategy(self, classification: str) -> Optional[str]:
        """Returns the recovery strategy with the highest success rate for a specific failure class."""
        try:
            cursor = self.coll_recovery.find(
                {"classification": classification, "success_rate": {"$gt": 0.5}}
            ).sort("success_rate", -1).limit(1)
            results = await cursor.to_list(length=1)
            if results:
                logger.info(f"Procedural Memory: Recommended best strategy for {classification}: '{results[0]['strategy']}' (Rate: {results[0]['success_rate']})")
                return results[0]["strategy"]
        except Exception as e:
            logger.error(f"Failed to get best recovery strategy: {e}")
        return None

    # ── 3. TOOL RELIABILITY METRICS ──────────────────────────────────────────

    async def record_tool_execution(self, tool_name: str, success: bool):
        """Updates executing tool statistics."""
        try:
            query = {"tool_name": tool_name}
            doc = await self.coll_tools.find_one(query)
            
            field_to_inc = "success_count" if success else "failure_count"
            
            if doc:
                succ = doc.get("success_count", 0) + (1 if success else 0)
                fail = doc.get("failure_count", 0) + (0 if success else 1)
                total = succ + fail
                
                await self.coll_tools.update_one(
                    query,
                    {
                        "$inc": {field_to_inc: 1},
                        "$set": {
                            "success_rate": round(succ / total, 3),
                            "updated_at": datetime.now()
                        }
                    }
                )
            else:
                await self.coll_tools.insert_one({
                    "tool_name": tool_name,
                    "success_count": 1 if success else 0,
                    "failure_count": 0 if success else 1,
                    "success_rate": 1.0 if success else 0.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
        except Exception as e:
            logger.error(f"Failed to record tool reliability: {e}")

    async def get_unreliable_tools(self, threshold: float = 0.7) -> List[str]:
        """Returns a list of tools whose success rate has fallen below the specified threshold."""
        try:
            cursor = self.coll_tools.find({"success_rate": {"$lt": threshold}})
            results = await cursor.to_list(length=100)
            return [r["tool_name"] for r in results]
        except Exception as e:
            logger.error(f"Failed to get unreliable tools: {e}")
            return []

    # ── 4. ENVIRONMENT PATTERNS (ANOMALIES & OVERRIDES) ──────────────────────

    async def record_environment_pattern(self, site: str, key: str, value: Any):
        """Stores environment settings, UI overrides, or anomaly records."""
        try:
            query = {"site": site.lower(), "key": key}
            await self.coll_env.update_one(
                query,
                {
                    "$set": {
                        "value": value,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            logger.info(f"Procedural Memory: Saved environmental pattern override: site={site}, {key}={value}")
        except Exception as e:
            logger.error(f"Failed to record environmental pattern: {e}")

    async def get_environment_pattern(self, site: str, key: str, default: Any = None) -> Any:
        """Retrieves a setting or selector override for a site."""
        try:
            doc = await self.coll_env.find_one({"site": site.lower(), "key": key})
            if doc:
                return doc.get("value", default)
        except Exception as e:
            logger.error(f"Failed to get environmental pattern: {e}")
        return default
