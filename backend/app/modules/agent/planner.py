"""
NOVA AI 2.0 — LLM-Powered Task Planner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Converts user goals into structured, executable multi-step plans.
Uses Groq LLaMA 3.3 70B with dynamic tool schema injection.
No hardcoded task templates — all plans generated dynamically.
"""

import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv
from app.modules.agent.capability_graph import CapabilityGraphEngine

load_dotenv()
logger = logging.getLogger("nova.planner")

# ── Planner System Prompt ──────────────────────────────────────
PLANNER_SYSTEM_PROMPT = """You are the Task Planner for NOVA AI, an autonomous operating system agent.

Your job: convert a user's goal into a structured JSON execution plan using ONLY the available tools.

RULES:
1. Output ONLY valid JSON — no markdown, no explanation, no commentary.
2. Each step must use a tool from the available tools list.
3. Parameters must match the tool's parameter schema exactly.
4. Steps execute sequentially — order matters.
5. Include an "expected_outcome" for each step so the system can verify success.
6. If a previous step outputs a file or resource, you can reference it in later steps using the dynamic state variable syntax: "$state.selected_resource_path"
7. If the goal is a simple conversational question (greeting, chat, knowledge question), return: {"type": "conversation", "response": "your brief answer"}
8. If the goal needs clarification, return: {"type": "clarification", "question": "what you need to know"}
9. For actionable tasks, return: {"type": "action", "goal": "...", "steps": [...]}
10. Keep plans minimal — use the fewest steps needed.
11. NEVER invent tools that aren't in the available list.

OUTPUT FORMAT for action plans:
{
  "type": "action",
  "goal": "brief goal summary",
  "steps": [
    {
      "step": 1,
      "tool": "fs_index_search",
      "parameters": {"query": "assignment pdf"},
      "expected_outcome": "finds the assignment"
    },
    {
      "step": 2,
      "tool": "browser_upload",
      "parameters": {"file": "$state.selected_resource_path"},
      "expected_outcome": "uploads the found file"
    }
  ]
}"""


class TaskPlanner:
    """
    LLM-powered task planner.
    Dynamically generates execution plans from user goals + available tools.
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.capability_graph = CapabilityGraphEngine()

    async def create_plan(self, goal: str, tools_schema: str,
                          context: str = None, past_workflows: list = None,
                          user_profile: dict = None) -> dict:
        """
        Generate an execution plan for a user goal.
        
        Args:
            goal: The user's request/goal
            tools_schema: Compact string of available tools (from registry)
            context: User context (name, preferences, memories)
            past_workflows: Similar past workflows for reference
            user_profile: The user profile dictionary containing settings
        
        Returns:
            Parsed plan dict with type, goal, and steps
        """
        messages = [{"role": "system", "content": PLANNER_SYSTEM_PROMPT}]

        # Inject available tools
        messages.append({
            "role": "system",
            "content": f"AVAILABLE TOOLS:\n{tools_schema}"
        })

        # Inject dynamic dependency rules from Capability Graph
        try:
            dep_rules = await self.capability_graph.get_dependency_rules_prompt()
            if dep_rules:
                messages.append({
                    "role": "system",
                    "content": f"STRUCTURAL CAPABILITY RULES & TOOL DEPENDENCIES:\n{dep_rules}\nStrictly follow these prerequisite and substitution guidelines when selecting steps."
                })
        except Exception:
            pass

        # Inject user context if available
        if context:
            messages.append({
                "role": "system",
                "content": f"USER CONTEXT:\n{context}"
            })

        # Inject past successful workflows as reference
        if past_workflows:
            ref = "\n".join([
                f"- Goal: \"{w['goal']}\" → Used tools: {[s['tool'] for s in w.get('plan', {}).get('steps', [])]}"
                for w in past_workflows[:3]
            ])
            messages.append({
                "role": "system",
                "content": f"SIMILAR PAST WORKFLOWS (for reference):\n{ref}"
            })

        messages.append({"role": "user", "content": goal})

        # Load preferences
        prefs = user_profile.get("preferences", {}) if user_profile else {}
        try:
            temp = float(prefs.get("cognitive_temp", 0.2))
        except Exception:
            temp = 0.2
            
        model_name = prefs.get("ai_model", "LLaMA 3.3 70B (Default)")
        model_mapping = {
            "LLaMA 3.3 70B (Default)": "llama-3.3-70b-versatile",
            "DeepSeek R1 (Reasoning)": "deepseek-r1-distill-llama-70b",
            "Gemini 1.5 Pro (Multi-modal)": "llama-3.3-70b-versatile",
            "GPT-4o (Omni)": "llama-3.3-70b-versatile"
        }
        active_model = model_mapping.get(model_name, "llama-3.3-70b-versatile")

        try:
            completion = self.client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temp,
                max_tokens=800,
                response_format={"type": "json_object"}  # Force JSON output
            )

            raw = completion.choices[0].message.content.strip()
            plan = json.loads(raw)

            # Validate plan structure
            plan = self._validate_plan(plan)

            # Apply Capability Graph verification and auto-patching
            try:
                plan = await self.capability_graph.verify_and_patch_plan(plan)
            except Exception as e:
                logger.warning(f"Capability Graph plan patching failed: {e}")

            logger.info(f"Plan generated: {plan.get('type')} with {len(plan.get('steps', []))} steps")
            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Planner JSON parse error: {e}")
            return {"type": "conversation", "response": "I had trouble planning that. Could you rephrase?"}
        except Exception as e:
            logger.error(f"Planner error: {e}")
            return {"type": "error", "error": str(e)}

    async def replan(self, original_goal: str, failed_step: dict,
                     observation: dict, tools_schema: str, current_state: dict = None,
                     user_profile: dict = None) -> dict:
        """
        Generate an alternative plan after a step failure.
        """
        messages = [{"role": "system", "content": PLANNER_SYSTEM_PROMPT}]
        messages.append({
            "role": "system",
            "content": f"AVAILABLE TOOLS:\n{tools_schema}"
        })
        
        if current_state:
            messages.append({
                "role": "system",
                "content": f"CURRENT TASK STATE (Working Memory):\n{json.dumps(current_state, indent=2)}\nUse the variables stored here (like $state.selected_resource_path) in your new plan if needed."
            })
            
        messages.append({
            "role": "user",
            "content": (
                f"Original goal: {original_goal}\n"
                f"Failed step: {json.dumps(failed_step)}\n"
                f"Failure reason: {observation.get('error', 'unknown')}\n"
                f"Recovery suggestion: {observation.get('suggestion', 'try alternative')}\n\n"
                f"Generate an ALTERNATIVE plan that avoids the failed approach."
            )
        })

        # Load preferences
        prefs = user_profile.get("preferences", {}) if user_profile else {}
        try:
            temp = float(prefs.get("cognitive_temp", 0.3))
        except Exception:
            temp = 0.3
            
        model_name = prefs.get("ai_model", "LLaMA 3.3 70B (Default)")
        model_mapping = {
            "LLaMA 3.3 70B (Default)": "llama-3.3-70b-versatile",
            "DeepSeek R1 (Reasoning)": "deepseek-r1-distill-llama-70b",
            "Gemini 1.5 Pro (Multi-modal)": "llama-3.3-70b-versatile",
            "GPT-4o (Omni)": "llama-3.3-70b-versatile"
        }
        active_model = model_mapping.get(model_name, "llama-3.3-70b-versatile")

        try:
            completion = self.client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temp,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content.strip()
            return self._validate_plan(json.loads(raw))
        except Exception as e:
            logger.error(f"Replan error: {e}")
            return {"type": "error", "error": str(e)}

    def _validate_plan(self, plan: dict) -> dict:
        """Validate and normalize plan structure."""
        plan_type = plan.get("type", "conversation")

        if plan_type == "action":
            steps = plan.get("steps", [])
            # Ensure each step has required fields
            validated_steps = []
            for i, step in enumerate(steps):
                validated_steps.append({
                    "step": step.get("step", i + 1),
                    "tool": step.get("tool", ""),
                    "parameters": step.get("parameters", {}),
                    "expected_outcome": step.get("expected_outcome", "")
                })
            plan["steps"] = validated_steps

        return plan
