import re
import logging
from app.modules.commands.dispatcher import CommandDispatcher
from app.modules.nlp.neural_engine import NeuralEngine
from app.modules.nlp.spacy_engine import SpacyEngine
from app.modules.memory.retriever import get_relevant_memories
from app.modules.agent.orchestrator import AgentOrchestrator
from app.core import state
from app.modules.user.user_manager import UserManager

logger = logging.getLogger("nova.processor")

class NLPProcessor:
    """
    Hybrid NLP pipeline (v2.0 — Agent-Augmented):
    - FAST PATH: spaCy detects simple commands (open/close/launch + app) → execute immediately.
    - AGENT PATH: Complex tasks → route to Agent Orchestrator (dynamic planning + tool execution).
    - LEGACY FALLBACK: If agent fails → falls back to original Neural Engine + Dispatcher.
    All previous features preserved — zero regression.
    """

    def __init__(self):
        self.dispatcher = CommandDispatcher()
        self.neural = NeuralEngine()
        self.spacy = SpacyEngine()
        self.user_manager = UserManager()
        self.orchestrator = AgentOrchestrator()

    async def analyze(self, text: str, user_profile: dict = None) -> dict:
        """
        Processes text using hybrid NLP and executes commands.
        """
        # Voice Switch Security - using natural language regex for STT
        switch_match = re.search(r"(?:user\s+switch|switch\s+user|switch\s+to|which).*?\b([a-zA-Z0-9_-]+)\b\s*confirm", text, re.IGNORECASE)
        if switch_match:
            new_user = switch_match.group(1).lower()
            if new_user == "gowri":
                new_user = "gauri"
            try:
                await self.user_manager.switch_active_user(new_user)
                return {
                    "intent": "SWITCH_USER",
                    "action": "user_switched",
                    "message": f"Active user context switched to {new_user}."
                }
            except Exception:
                return {
                    "intent": "SWITCH_USER",
                    "action": "switch_failed",
                    "message": "User switch failed. Invalid user."
                }

        user_id = user_profile.get("user_id", state.ACTIVE_USER) if user_profile else state.ACTIVE_USER

        # ── BUILD USER CONTEXT (shared by agent + legacy) ─────
        relevant_memories = await get_relevant_memories(user_id, text, k=3)
        
        user_name = user_profile.get("name", user_id) if user_profile else user_id
        prefs = user_profile.get("preferences", {}) if user_profile else {}
        
        context_parts = [
            f"Active User Context:",
            f"- Name: {user_name}",
            f"- Theme: {prefs.get('theme', 'dark')}",
            f"- Default Browser: {prefs.get('browser', 'chrome')}",
            f"- Music: {prefs.get('music', 'spotify')}"
        ]
        
        if relevant_memories:
            context_parts.append("\nRelevant Memories:")
            context_parts.extend([f"- {m}" for m in relevant_memories])
            
        context_str = "\n".join(context_parts)

        # ── AGENT PATH: Autonomous Agent Orchestrator ─────────
        # Routes complex tasks through the dynamic planner + tool system
        try:
            agent_result = await self.orchestrator.execute_goal(
                goal=text,
                user_id=user_id,
                context=context_str
            )
            
            # If agent handled it successfully, return its result
            if agent_result.get("intent") not in ("ERROR",):
                logger.info(f"Agent handled: {agent_result.get('intent')} via {agent_result.get('action')}")
                return agent_result
                
        except Exception as e:
            logger.warning(f"Agent orchestrator failed, falling back to legacy: {e}")

        # ── LEGACY FALLBACK: Original Neural Engine Path ──────
        # Kept intact for backward compatibility and as safety net
        ai_response = await self.neural.get_response(text, context=context_str, user_profile=user_profile)

        # Check if the AI wants to execute an action
        # Format: [ACTION:INTENT:PARAM1:PARAM2:PARAM3]
        action_matches = list(re.finditer(r"\[ACTION:(\w+)(?::([^\]]*))?\]", ai_response))

        intent = "CONVERSATION"
        action = "neural_reply"
        
        # Clean the message by removing all [ACTION:...] tags
        message = re.sub(r"\[ACTION:[^\]]*\]", "", ai_response).strip()

        if action_matches:
            intent = "MULTI_ACTION" if len(action_matches) > 1 else action_matches[0].group(1)
            action = "sequence_exec" if len(action_matches) > 1 else "single_exec"
            
            for match in action_matches:
                curr_intent = match.group(1)
                params_str = match.group(2) or ""
                params_list = params_str.split(":")

                # Execute the detected intent
                if curr_intent == "SWITCH_USER":
                    new_user = params_list[0].lower() if params_list else "amarnath"
                    if new_user == "gowri": new_user = "gauri"
                    try:
                        await self.user_manager.switch_active_user(new_user)
                        if not message:
                            message = f"User profile switched to {new_user}."
                    except Exception:
                        if not message:
                            message = "Failed to switch user profile."

                elif curr_intent == "OPEN_APP":
                    app = params_list[0] if params_list else ""
                    exec_msg = await self.dispatcher.execute("OPEN_APP", {"entity": app})
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "OPEN_WEBSITE":
                    url = params_str  # URLs can contain colons, do not use params_list[0]
                    await self.dispatcher.execute("OPEN_WEBSITE", {"url": url})

                elif curr_intent == "POWERSHELL_CMD":
                    script = params_str  # Scripts can contain colons, do not use params_list[0]
                    exec_msg = await self.dispatcher.execute("POWERSHELL_CMD", {"script": script})
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "WEB_SEARCH":
                    query = params_str  # Queries might contain colons
                    await self.dispatcher.execute("WEB_SEARCH", {"query": query})

                elif curr_intent == "CREATE_NOTE":
                    filename = params_list[0] if len(params_list) > 0 else None
                    content = params_list[1] if len(params_list) > 1 else text
                    location = params_list[2] if len(params_list) > 2 else "vault"
                    exec_msg = await self.dispatcher.execute("CREATE_NOTE", {
                        "content": content, 
                        "filename": filename,
                        "location": f"vault/{user_id}" if location == "vault" else location
                    })
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "CREATE_FOLDER":
                    folder = params_list[0] if len(params_list) > 0 else ""
                    location = params_list[1] if len(params_list) > 1 else "desktop"
                    exec_msg = await self.dispatcher.execute("CREATE_FOLDER", {
                        "entity": folder,
                        "location": location
                    })
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "LIST_VAULT":
                    exec_msg = await self.dispatcher.execute("LIST_VAULT", {"user_id": user_id})
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "SYSTEM_INFO":
                    exec_msg = await self.dispatcher.execute("SYSTEM_INFO", {})
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "OPEN_FOLDER":
                    folder = params_list[0] if params_list else ""
                    exec_msg = await self.dispatcher.execute("OPEN_FOLDER", {"entity": folder})
                    message = f"{message} {exec_msg}".strip()

                elif curr_intent == "CLOSE_APP":
                    app = params_list[0] if params_list else ""
                    exec_msg = await self.dispatcher.execute("CLOSE_APP", {"entity": app})
                    message = f"{message} {exec_msg}".strip()

        return {
            "intent": intent,
            "action": action,
            "message": message
        }
