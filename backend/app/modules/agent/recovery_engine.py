"""
NOVA AI 2.0 — Recovery & Replanning Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intelligent self-healing system that analyzes execution failures, classifies
them into environmental/system anomalies, and applies structured recovery strategies.

Features:
1. Understanding WHY (failure classifications)
2. Strategic Recovery Selection (backoff retries, FTS file searches, selector correction, parameter self-correction)
3. In-place Queue Patching (step injection, dynamic state corrections)
4. Graceful LLM replanning fallback
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from groq import Groq
from app.modules.observation.observer import Observation

logger = logging.getLogger("nova.recovery")


@dataclass
class RecoveryDecision:
    """Outcome of the recovery engine analysis."""
    action: str                        # "retry_step", "inject_steps", "replan", "abort"
    name: str                          # Name of the recovery strategy applied
    classification: str                # Failure classification
    delay_seconds: int = 0             # Delay before executing the next step
    patched_params: Optional[dict] = None  # Corrected params for retried tool
    injected_steps: List[dict] = field(default_factory=list)  # Steps to inject before the retry
    message: str = ""                  # User-friendly explanation


class RecoveryEngine:
    """
    Autonomously resolves tool execution failures by patching plans and state variables.
    """

    def __init__(self, planner_client: Optional[Groq] = None):
        self.client = planner_client or Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
        # Track recovery attempt counts per step key to avoid infinite loops
        # format: { "step_tool_name": attempt_count }
        self._recovery_counts: Dict[str, int] = {}
        
        from app.modules.memory.procedural_memory import ProceduralMemoryEngine
        self.procedural_memory = ProceduralMemoryEngine(groq_client=self.client)

    def reset_recovery_history(self):
        """Clears recovery counts for a new goal/task session."""
        self._recovery_counts.clear()

    async def record_recovery_outcome(self, classification: str, strategy: str, success: bool):
        """Record recovery outcome in procedural memory."""
        try:
            await self.procedural_memory.record_recovery_outcome(classification, strategy, success)
        except Exception as e:
            logger.error(f"Failed to save recovery outcome: {e}")

    def _get_recovery_key(self, tool_name: str, step_num: int) -> str:
        return f"{tool_name}_{step_num}"

    async def analyze_and_recover(self, 
                                  tool_name: str, 
                                  params: dict, 
                                  observation: Observation, 
                                  state: Any, 
                                  step_queue: List[dict],
                                  tools_schema: str) -> RecoveryDecision:
        """
        Analyzes a step failure, classifies it, selects a recovery strategy,
        and returns a decision containing actions to repair the queue.
        """
        step_num = state.current_step
        rec_key = self._get_recovery_key(tool_name, step_num)
        attempts = self._recovery_counts.get(rec_key, 0) + 1
        self._recovery_counts[rec_key] = attempts

        error_msg = (observation.error or "").lower()
        hints = observation.recovery_hints or []

        logger.warning(f"Recovery Engine analyzing failure: tool={tool_name}, attempt={attempts}, error={error_msg}")

        # Limit recovery attempts for a single step
        if attempts > 3:
            logger.error(f"Max recovery attempts ({attempts-1}) exceeded for step {step_num} ({tool_name}). Forcing full replan.")
            return RecoveryDecision(
                action="replan",
                name="MaxAttemptsExceeded",
                classification="RECURSION_LIMIT",
                message="Multiple recovery strategies failed. Triggering dynamic plan redesign."
            )

        # ── 1. CLASSIFY FAILURE ──────────────────────────────────────────────
        classification = self._classify_failure(tool_name, error_msg, hints, observation)
        logger.info(f"Failure classified as: {classification}")

        # ── 2. EXECUTE STRATEGY SELECTION ────────────────────────────────────

        # Strategy A: NETWORK_ERROR -> Transient exponential backoff retry
        if classification == "NETWORK_ERROR":
            delay = 5 * attempts  # 5s, 10s, 15s
            return RecoveryDecision(
                action="retry_step",
                name="NetworkExponentialBackoff",
                classification=classification,
                delay_seconds=delay,
                message=f"Network latency or timeout detected. Waiting {delay} seconds before retrying..."
            )

        # Strategy B: AUTH_ERROR / CAPTCHA -> Human-in-the-loop validation
        if classification == "AUTH_ERROR":
            logger.info("Auth/CAPTCHA blocked. Initiating human-in-the-loop delay sensor...")
            # We wait for up to 30 seconds for the user to solve it. We do progressive 5s polling checks.
            solved = False
            browser_page = None
            try:
                from app.modules.agent.tools.browser_tools import _browser_ctrl
                if _browser_ctrl and _browser_ctrl._initialized:
                    browser_page = await _browser_ctrl._ensure_page()
            except Exception:
                pass

            if browser_page:
                for check in range(6):
                    await asyncio.sleep(5.0)
                    body_text = (await browser_page.inner_text("body")).lower()
                    # Check if anomaly primitives are cleared
                    has_captcha = any(p in body_text for p in ["captcha", "verify you are human", "robot"])
                    if not has_captcha:
                        solved = True
                        break
            
            if solved:
                return RecoveryDecision(
                    action="retry_step",
                    name="HumanInterventionResolved",
                    classification=classification,
                    message="Security screen resolved by user. Resuming tool execution immediately."
                )
            else:
                return RecoveryDecision(
                    action="replan",
                    name="HumanInterventionTimeout",
                    classification=classification,
                    message="Timed out waiting for manual security verification. Replanning alternate task approach."
                )

        # Strategy C: RESOURCE_ERROR -> Vector FTS Filesystem search & injection
        if classification == "RESOURCE_ERROR":
            # If a file is missing, try to search for it using FTS index search, then retry this step
            missing_file = params.get("path") or params.get("file") or params.get("filepath") or ""
            if missing_file and isinstance(missing_file, str):
                file_basename = os.path.basename(missing_file)
                logger.info(f"Missing file identified: {file_basename}. Injecting fs_index_search...")
                
                # Create FTS search step to locate the file
                search_step = {
                    "step": step_num,
                    "tool": "fs_index_search",
                    "parameters": {"query": file_basename},
                    "expected_outcome": "locate the actual location of the missing file"
                }
                
                # Let's adjust parameters of the retry tool to refer to the located state path
                retry_params = dict(params)
                for k, v in retry_params.items():
                    if v == missing_file:
                        retry_params[k] = "$state.selected_resource_path"
                
                return RecoveryDecision(
                    action="inject_steps",
                    name="FtsIndexFileRecovery",
                    classification=classification,
                    injected_steps=[search_step],
                    patched_params=retry_params,
                    message=f"I couldn't locate '{file_basename}'. Injecting an indexed semantic search to locate the correct file path."
                )

        # Strategy D: UI_SELECTOR_ERROR -> Context extraction & alternative selectors
        if classification == "UI_SELECTOR_ERROR":
            # Inject a browser context extraction step to extract text/links, helping the AI find alternative selectors
            logger.info("Playwright selector missing. Injecting browser_extract_text to find alternative links...")
            extract_step = {
                "step": step_num,
                "tool": "browser_extract_text",
                "parameters": {},
                "expected_outcome": "extract all page elements to find valid interactables"
            }
            return RecoveryDecision(
                action="inject_steps",
                name="UiSelectorContextRecovery",
                classification=classification,
                injected_steps=[extract_step],
                message="HTML element not found. Extracting the page text context to auto-correct the interaction target."
            )

        # Strategy E: Adaptive Tool Substitution (using the Capability Graph)
        if attempts == 2:
            try:
                from app.modules.agent.capability_graph import CapabilityGraphEngine
                cap_graph = CapabilityGraphEngine()
                substitutes = await cap_graph.get_substitutes(tool_name)
                
                if substitutes:
                    sub_tool = substitutes[0]
                    logger.info(f"Adaptive Orchestration: Dynamic tool substitution selected: '{tool_name}' -> '{sub_tool}'")
                    
                    # Create alternative step
                    sub_step = {
                        "step": step_num,
                        "tool": sub_tool,
                        "parameters": params,
                        "expected_outcome": f"Substitute tool '{sub_tool}' after '{tool_name}' failure"
                    }
                    
                    return RecoveryDecision(
                        action="inject_steps",
                        name="AdaptiveToolSubstitution",
                        classification=classification,
                        injected_steps=[sub_step],
                        message=f"I encountered a failure with '{tool_name}'. Dynamically switching to alternative capability '{sub_tool}' to complete the workflow."
                    )
            except Exception as e:
                logger.warning(f"Adaptive Tool Substitution lookup failed: {e}")

        # Strategy F: SELF_CORRECTION -> Parameter LLM Correction
        if classification in ["SYNTAX_ERROR", "API_LIMIT_ERROR"] or attempts >= 2:
            # Let LLaMA correct the parameters if it seems like a syntax error or a bad argument
            logger.info("Syntax or complex error detected. Invoking LLaMA Parameter Self-Correction...")
            corrected_params = await self._correct_parameters_via_llm(
                tool_name=tool_name,
                params=params,
                error=error_msg,
                tools_schema=tools_schema
            )
            
            if corrected_params and corrected_params != params:
                logger.info(f"Self-correction succeeded! Patched params: {corrected_params}")
                return RecoveryDecision(
                    action="retry_step",
                    name="LlamaParameterSelfCorrection",
                    classification=classification,
                    patched_params=corrected_params,
                    message="I detected a parameter syntax error. Self-corrected the inputs and retrying the operation."
                )

        # Default fallback: Replan
        return RecoveryDecision(
            action="replan",
            name="DefaultReplanner",
            classification=classification,
            message="Complex execution block encountered. Redeploying task planner to patch the remaining steps."
        )

    def _classify_failure(self, tool_name: str, error_msg: str, hints: List[str], observation: Observation) -> str:
        """Categorize failures based on keywords and observation properties."""
        if observation.anomaly_detected or "captcha" in error_msg or "expired" in error_msg:
            return "AUTH_ERROR"
            
        if "network" in error_msg or "timeout" in error_msg or "offline" in error_msg or "dns" in error_msg:
            return "NETWORK_ERROR"

        if "not found" in error_msg or "no such file" in error_msg or "file_not_found" in error_msg:
            return "RESOURCE_ERROR"

        if "selector" in error_msg or "locator" in error_msg or "element" in error_msg or "xpath" in error_msg:
            return "UI_SELECTOR_ERROR"

        if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
            return "API_LIMIT_ERROR"

        if "typeerror" in error_msg or "valueerror" in error_msg or "argument" in error_msg or "invalid parameters" in error_msg:
            return "SYNTAX_ERROR"

        # Check hints mapping
        if "verify_file_path" in hints or "run_filesystem_search" in hints:
            return "RESOURCE_ERROR"
        if "try_alternative_selector" in hints or "extract_text_context" in hints:
            return "UI_SELECTOR_ERROR"
        if "check_network_connection" in hints:
            return "NETWORK_ERROR"

        return "UNKNOWN_ERROR"

    async def _correct_parameters_via_llm(self, tool_name: str, params: dict, error: str, tools_schema: str) -> Optional[dict]:
        """
        Uses Groq LLaMA to repair argument syntax, correct relative paths to absolute,
        and align parameters with the active registry schema.
        """
        prompt = f"""You are the Parameter Self-Correction Engine for NOVA AI.
A tool execution has failed due to incorrect parameter values or syntax.
Your task is to analyze the error, review the target tool schema, and output a corrected parameter JSON dictionary.

Target Tool: {tool_name}
Failed Parameters: {json.dumps(params, indent=2)}
Error Received: {error}

AVAILABLE TOOL SPECIFICATIONS:
{tools_schema}

INSTRUCTIONS:
1. Output ONLY a valid JSON dictionary representing the corrected parameters.
2. Do NOT add markdown, explanations, or commentary.
3. Keep all valid parameters intact and only correct the elements causing the syntax or schema violation.
4. If a file path is relative and causing an error, convert it to a standard Windows path if you can infer the user context.

Corrected Parameter JSON:"""

        try:
            # We run this in an executor to avoid blocking the async event loop
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Ultra-low temperature for precision
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content.strip()
            corrected = json.loads(raw)
            return corrected
        except Exception as e:
            logger.error(f"Parameter self-correction LLM call failed: {e}")
            return None

