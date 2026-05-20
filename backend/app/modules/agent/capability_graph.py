"""
NOVA AI 2.0 — Capability Graph Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Teaches NOVA relational orchestration intelligence, mapping tool dependencies,
clustering capability zones, and enabling dynamic workflow synthesis & tool substitution.
"""

import os
import certifi
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("nova.capability_graph")


class CapabilityGraphEngine:
    """
    Orchestrates capabilities as a directed dependency graph, enabling structural
    reasoning, topological pathfinding, and automated tool substitution.
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
        self.collection = self.db["agent_capability_graph"]
        self._local_cache: Dict[str, dict] = {}

    async def initialize_default_graph(self):
        """Seeds the database with default capability nodes if they do not exist."""
        try:
            default_nodes = [
                # ── Filesystem Cluster ──
                {
                    "name": "fs_index_search",
                    "cluster": "filesystem",
                    "requires": [],
                    "provides": ["selected_resource_path"],
                    "substitutes": ["resolve_resource", "filesystem_list"],
                    "description": "Searches and locates files using local vector index"
                },
                {
                    "name": "resolve_resource",
                    "cluster": "filesystem",
                    "requires": [],
                    "provides": ["selected_resource_path"],
                    "substitutes": ["fs_index_search"],
                    "description": "Resolves ambiguous query terms to absolute file paths"
                },
                {
                    "name": "fs_read",
                    "cluster": "filesystem",
                    "requires": ["selected_resource_path"],
                    "provides": ["file_content"],
                    "substitutes": [],
                    "description": "Reads contents of a local file resource"
                },
                {
                    "name": "fs_write",
                    "cluster": "filesystem",
                    "requires": [],
                    "provides": ["written_file_path"],
                    "substitutes": [],
                    "description": "Writes text or data to a specified local file path"
                },
                # ── Browser Cluster ──
                {
                    "name": "browser_open",
                    "cluster": "browser",
                    "requires": [],
                    "provides": ["browser_open"],
                    "substitutes": [],
                    "description": "Launches a new browser automation instance"
                },
                {
                    "name": "browser_navigate",
                    "cluster": "browser",
                    "requires": ["browser_open"],
                    "provides": ["page_loaded"],
                    "substitutes": [],
                    "description": "Navigates to a specific URL in the active browser"
                },
                {
                    "name": "browser_click",
                    "cluster": "browser",
                    "requires": ["browser_open"],
                    "provides": [],
                    "substitutes": [],
                    "description": "Clicks an element identified by selector in active page"
                },
                {
                    "name": "browser_type",
                    "cluster": "browser",
                    "requires": ["browser_open"],
                    "provides": [],
                    "substitutes": [],
                    "description": "Types text into a selector-specified field in browser"
                },
                {
                    "name": "browser_upload",
                    "cluster": "browser",
                    "requires": ["browser_open", "selected_resource_path"],
                    "provides": ["upload_success"],
                    "substitutes": ["email_send", "discord_send"],
                    "description": "Uploads a resource file to a dynamic website dropzone"
                },
                {
                    "name": "browser_extract_text",
                    "cluster": "browser",
                    "requires": ["browser_open"],
                    "provides": ["extracted_text"],
                    "substitutes": [],
                    "description": "Extracts text content or DOM elements from web page"
                },
                # ── Communication Cluster ──
                {
                    "name": "discord_send",
                    "cluster": "communication",
                    "requires": ["resolved_contact"],
                    "provides": ["message_sent"],
                    "substitutes": ["email_send", "whatsapp_send"],
                    "description": "Dispatches a message/media attachment via Discord"
                },
                {
                    "name": "email_send",
                    "cluster": "communication",
                    "requires": ["resolved_contact"],
                    "provides": ["message_sent"],
                    "substitutes": ["discord_send", "whatsapp_send"],
                    "description": "Dispatches an email containing text or attachment files"
                },
                {
                    "name": "whatsapp_send",
                    "cluster": "communication",
                    "requires": ["resolved_contact"],
                    "provides": ["message_sent"],
                    "substitutes": ["discord_send", "email_send"],
                    "description": "Dispatches a message/media attachment via WhatsApp API"
                },
                # ── System Cluster ──
                {
                    "name": "launch_app",
                    "cluster": "system",
                    "requires": [],
                    "provides": ["app_open"],
                    "substitutes": [],
                    "description": "Launches a desktop operating system application"
                },
                {
                    "name": "shell_command",
                    "cluster": "system",
                    "requires": [],
                    "provides": ["command_output"],
                    "substitutes": [],
                    "description": "Executes shell commands on host operating system securely"
                }
            ]

            for node in default_nodes:
                await self.collection.update_one(
                    {"name": node["name"]},
                    {"$setOnInsert": node},
                    upsert=True
                )
            logger.info("Capability Graph Engine: Default nodes initialized successfully")
            await self.load_cache()
        except Exception as e:
            logger.error(f"Failed to initialize default capability graph: {e}")

    async def load_cache(self):
        """Loads capability graph database records into memory for high-performance lookups."""
        try:
            cursor = self.collection.find({})
            results = await cursor.to_list(length=100)
            self._local_cache = {doc["name"]: doc for doc in results}
            logger.info(f"Capability Graph: Loaded {len(self._local_cache)} capabilities into memory cache")
        except Exception as e:
            logger.error(f"Failed to load capability cache: {e}")

    async def register_capability(self, name: str, cluster: str,
                                  requires: List[str], provides: List[str],
                                  substitutes: List[str], description: str):
        """Dynamically registers or updates a capability node in the graph."""
        try:
            doc = {
                "name": name,
                "cluster": cluster,
                "requires": requires,
                "provides": provides,
                "substitutes": substitutes,
                "description": description,
                "updated_at": datetime.now()
            }
            await self.collection.update_one(
                {"name": name},
                {"$set": doc},
                upsert=True
            )
            self._local_cache[name] = doc
            logger.info(f"Capability Graph: Successfully registered/updated tool node '{name}'")
        except Exception as e:
            logger.error(f"Failed to register capability '{name}': {e}")

    async def get_substitutes(self, tool_name: str) -> List[str]:
        """Returns compatible tools capable of substituting the target tool."""
        if not self._local_cache:
            await self.load_cache()
        node = self._local_cache.get(tool_name)
        return node.get("substitutes", []) if node else []

    async def get_cluster_tools(self, cluster: str) -> List[str]:
        """Returns all capability names associated with a capability cluster zone."""
        if not self._local_cache:
            await self.load_cache()
        return [name for name, node in self._local_cache.items() if node.get("cluster") == cluster]

    async def get_dependency_rules_prompt(self) -> str:
        """
        Generates a structured dynamic text prompt representing structural tool dependency rules
        to guide and restrict LLM planners.
        """
        if not self._local_cache:
            await self.load_cache()
        
        rules = []
        for name, node in self._local_cache.items():
            reqs = node.get("requires", [])
            subs = node.get("substitutes", [])
            if reqs:
                rules.append(f"- Tool '{name}' REQUIRES the following prerequisite step(s) or outputs beforehand: {', '.join(reqs)}")
            if subs:
                rules.append(f"- Tool '{name}' has alternative substitutes if it fails: {', '.join(subs)}")
        
        return "\n".join(rules) if rules else "No static dependency rules registered."

    async def compose_workflow(self, target_capability: str) -> List[str]:
        """
        Resolves dynamic topological pathways using Depth First Search (DFS)
        to compose a required sequence of dependency tools.
        """
        if not self._local_cache:
            await self.load_cache()

        visited: Set[str] = set()
        temp_marked: Set[str] = set()
        workflow: List[str] = []

        def dfs(node_name: str):
            if node_name in temp_marked:
                raise ValueError(f"Circular dependency anomaly detected in capability node: '{node_name}'")
            if node_name not in visited:
                temp_marked.add(node_name)
                node = self._local_cache.get(node_name)
                if node:
                    # Satisfy prerequisites first
                    for req in node.get("requires", []):
                        # Map generalized requirements to concrete tools providing them
                        prereq_tools = self._resolve_tools_for_requirement(req)
                        for p_tool in prereq_tools:
                            dfs(p_tool)
                temp_marked.remove(node_name)
                visited.add(node_name)
                workflow.append(node_name)

        try:
            dfs(target_capability)
            return workflow
        except Exception as e:
            logger.error(f"Topological pathway composition failed for '{target_capability}': {e}")
            return [target_capability]

    def _resolve_tools_for_requirement(self, requirement: str) -> List[str]:
        """Maps output requirements (like 'browser_open') back to specific tools supplying them."""
        matches = []
        for name, node in self._local_cache.items():
            if requirement in node.get("provides", []) or name == requirement:
                matches.append(name)
        return matches if matches else [requirement]

    async def verify_and_patch_plan(self, plan: dict) -> dict:
        """
        Structural reasoning engine that reviews step pipelines, validates execution
        dependencies, and auto-patches plan blocks with missing pre-requisites.
        """
        if plan.get("type") != "action":
            return plan

        if not self._local_cache:
            await self.load_cache()

        steps = plan.get("steps", [])
        if not steps:
            return plan

        satisfied_states: Set[str] = set()
        patched_steps: List[dict] = []
        step_counter = 1

        for step in steps:
            tool = step.get("tool", "")
            node = self._local_cache.get(tool)
            
            if node:
                prereqs = node.get("requires", [])
                for prereq in prereqs:
                    # Check if requirement has been satisfied in prior steps
                    if prereq not in satisfied_states:
                        # Auto-resolve dependency tool and inject it in-place
                        dependency_tools = self._resolve_tools_for_requirement(prereq)
                        if dependency_tools:
                            dep_tool = dependency_tools[0]
                            dep_node = self._local_cache.get(dep_tool)
                            
                            # Construct and inject step
                            injected_step = {
                                "step": step_counter,
                                "tool": dep_tool,
                                "parameters": {},
                                "expected_outcome": f"Injected dependency to satisfy '{prereq}'"
                            }
                            # Populate provides state
                            if dep_node:
                                for prov in dep_node.get("provides", []):
                                    satisfied_states.add(prov)
                            satisfied_states.add(dep_tool)
                            
                            patched_steps.append(injected_step)
                            logger.info(f"Capability Graph: Auto-injected dependency '{dep_tool}' before executing '{tool}'")
                            step_counter += 1

                # Satisfy active tool outputs
                for prov in node.get("provides", []):
                    satisfied_states.add(prov)
                satisfied_states.add(tool)

            # Keep original step but adjust step counter
            step["step"] = step_counter
            patched_steps.append(step)
            step_counter += 1

        plan["steps"] = patched_steps
        return plan
