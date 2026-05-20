"""
NOVA AI 2.0 — Dynamic Tool Synthesis Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Empowers NOVA with self-extending capability cognition, enabling on-the-fly Python tool
generation, sandboxed validation, self-correcting compilations, dynamic imports, and promotion.
"""

import os
import sys
import importlib.util
import py_compile
import certifi
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from motor.motor_asyncio import AsyncIOMotorClient
from groq import Groq
from dotenv import load_dotenv

from app.modules.agent.tools.base_tool import BaseTool
from app.modules.agent.tools.registry import get_registry

load_dotenv()
# Initialize logger for dynamic tool synthesis
logger = logging.getLogger("nova.tool_synthesis")


class DynamicToolSynthesisEngine:
    """
    Generative capability engine that dynamically designs, compiles, validates,
    and registers persistent or temporary tools to solve complex/custom objectives.
    """

    def __init__(self, groq_client: Optional[Groq] = None):
        ca = certifi.where()
        self.db_client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.db_client[os.getenv("DATABASE_NAME", "nova_ai")]
        self.collection = self.db["agent_dynamic_tools"]
        
        self.groq_client = groq_client or Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
        # Paths
        self.dynamic_dir = os.path.join(
            os.getcwd(), "backend", "app", "modules", "agent", "tools", "dynamic"
        )
        os.makedirs(self.dynamic_dir, exist_ok=True)
        # Create an __init__.py inside the dynamic tools folder to make it an importable package
        init_file = os.path.join(self.dynamic_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# NOVA Dynamic Synthesized Tools Package\n")

    async def load_promoted_tools(self):
        """Loads and imports all promoted dynamic tools from MongoDB on startup."""
        try:
            cursor = self.collection.find({"promoted": True})
            promoted_docs = await cursor.to_list(length=100)
            
            for doc in promoted_docs:
                filename = doc.get("filename")
                if filename:
                    file_path = os.path.join(self.dynamic_dir, filename)
                    if os.path.exists(file_path):
                        await self._load_tool_from_file(file_path)
            logger.info(f"Dynamic Tool Synthesis: Loaded {len(promoted_docs)} promoted tools on startup.")
        except Exception as e:
            logger.error(f"Failed to load promoted tools on startup: {e}")

    async def synthesize_and_register(self, tool_name: str, objective: str,
                                      parameters: Dict[str, str], category: str = "custom") -> Optional[BaseTool]:
        """
        Synthesizes a new capability tool on the fly, validates it, and registers it.
        """
        logger.info(f"Synthesizing dynamic tool '{tool_name}' for objective: {objective}")
        
        attempts = 1
        code = await self._generate_tool_code(tool_name, objective, parameters, category)
        
        while attempts <= 3:
            # 1. Save temporary script
            filename = f"dyn_{tool_name}.py"
            file_path = os.path.join(self.dynamic_dir, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 2. Syntax Compile Check
            compile_error = self._verify_syntax(file_path)
            
            if not compile_error:
                # 3. Dynamic Load Validation
                try:
                    tool_instance = await self._load_tool_from_file(file_path)
                    if tool_instance:
                        # Success! Record metadata in MongoDB
                        await self.collection.update_one(
                            {"name": tool_name},
                            {
                                "$set": {
                                    "name": tool_name,
                                    "filename": filename,
                                    "objective": objective,
                                    "parameters": parameters,
                                    "category": category,
                                    "promoted": False,
                                    "success_count": 0,
                                    "execution_count": 0,
                                    "created_at": datetime.now(),
                                    "updated_at": datetime.now()
                                }
                            },
                            upsert=True
                        )
                        logger.info(f"Dynamic Tool Synthesis: Tool '{tool_name}' successfully compiled and registered!")
                        return tool_instance
                except Exception as e:
                    compile_error = str(e)

            # Self-Correction Loop
            logger.warning(f"Dynamic tool '{tool_name}' compilation failed: {compile_error}. Attempting Self-Correction {attempts}/3...")
            code = await self._self_correct_tool_code(code, compile_error)
            attempts += 1
            
        logger.error(f"Failed to synthesize valid tool '{tool_name}' after 3 attempts.")
        return None

    async def promote_tool(self, tool_name: str):
        """Promotes a successful dynamic tool to a persistent, permanent capability."""
        try:
            doc = await self.collection.find_one({"name": tool_name})
            if doc:
                await self.collection.update_one(
                    {"name": tool_name},
                    {"$set": {"promoted": True, "updated_at": datetime.now()}}
                )
                logger.info(f"Dynamic Tool Synthesis: Tool '{tool_name}' successfully promoted to persistent capability!")
        except Exception as e:
            logger.error(f"Failed to promote tool '{tool_name}': {e}")

    async def record_tool_execution(self, tool_name: str, success: bool):
        """Monitors dynamic tool outcomes and automatically promotes tools that prove high reliability."""
        try:
            doc = await self.collection.find_one({"name": tool_name})
            if doc:
                count = doc.get("execution_count", 0) + 1
                succs = doc.get("success_count", 0) + (1 if success else 0)
                rate = succs / count
                
                updates: Dict[str, Any] = {
                    "execution_count": count,
                    "success_count": succs,
                    "success_rate": round(rate, 2),
                    "updated_at": datetime.now()
                }
                
                # Auto-promote tool if it succeeds 3 times with 100% success rate
                if count >= 3 and rate >= 1.0 and not doc.get("promoted", False):
                    updates["promoted"] = True
                    logger.info(f"Dynamic Tool Synthesis: Auto-promoting highly reliable tool '{tool_name}'!")

                await self.collection.update_one({"name": tool_name}, {"$set": updates})
        except Exception as e:
            logger.error(f"Failed to record dynamic tool execution: {e}")

    def _verify_syntax(self, file_path: str) -> Optional[str]:
        """Runs py_compile compilation syntax checks to ensure zero Python syntax errors."""
        try:
            py_compile.compile(file_path, doraise=True)
            return None
        except Exception as e:
            return str(e)

    async def _load_tool_from_file(self, file_path: str) -> Optional[BaseTool]:
        """Dynamically imports a tool module at runtime and registers it in the registry."""
        module_name = os.path.basename(file_path).replace(".py", "")
        spec = importlib.util.spec_from_file_location(
            f"app.modules.agent.tools.dynamic.{module_name}", file_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Locate classes inheriting from BaseTool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and attr != BaseTool
                    and issubclass(attr, BaseTool)
                ):
                    tool_instance = attr()
                    get_registry().register(tool_instance)
                    logger.info(f"Dynamic Tool Synthesis: Successfully registered module class: '{attr_name}'")
                    return tool_instance
        return None

    async def _generate_tool_code(self, tool_name: str, objective: str,
                                  parameters: Dict[str, str], category: str) -> str:
        """Invokes LLaMA to write highly structured Python code extending BaseTool."""
        prompt = f"""You are the Dynamic Tool Synthesis Engine for NOVA AI.
Your job is to generate a fully valid, self-contained Python module defining a single tool class that inherits from `BaseTool`.
The tool is designed to solve this precise objective: "{objective}"
Parameters required: {parameters}
Tool Name (name property): "{tool_name}"
Tool Category: "{category}"

RULES:
1. Return ONLY the raw Python code block. Do NOT include markdown code blocks (like ```python), explanations, or commentary.
2. The module must import:
   from app.modules.agent.tools.base_tool import BaseTool, ToolResult
3. You must subclass `BaseTool`. The subclass must implement:
   - @property name(self) -> str
   - @property description(self) -> str
   - @property parameters(self) -> dict
   - @property category(self) -> str
   - async def execute(self, **kwargs) -> ToolResult
4. Keep dependencies clean. Use standard library or httpx/asyncio/playwright where appropriate.
5. In execute(), catch all internal exceptions and return a failed ToolResult(success=False, error=str(e)).
6. Do NOT call get_registry().register() at the bottom. The system loader handles class instantiations automatically.

Write the complete Python tool module:"""

        completion = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Strict temperature for high syntax precision
            max_tokens=1500
        )
        return completion.choices[0].message.content.strip()

    async def _self_correct_tool_code(self, original_code: str, error_msg: str) -> str:
        """Self-correcting compilation fallback mapping output errors back to LLaMA for code patches."""
        prompt = f"""You are the Python Code Refactoring Expert for NOVA AI.
A dynamically generated tool module has failed syntax compilation or verification.
Your task is to analyze the error, repair the original code, and return the corrected complete Python module.

Failed Python Code:
{original_code}

Compiler Error Received:
{error_msg}

INSTRUCTIONS:
1. Return ONLY the corrected, clean Python code block. Do NOT include markdown code blocks, explanation, or commentary.
2. Ensure it subclasses BaseTool correctly and satisfies all imports.

Corrected Python Code:"""

        completion = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        return completion.choices[0].message.content.strip()
