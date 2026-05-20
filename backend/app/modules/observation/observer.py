"""
NOVA AI 2.0 — Advanced Observation Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evolved post-action verification system with environmental awareness.
Analyzes outcomes across multiple layers (DOM, System, Visual),
scores confidence based on concrete evidence, handles temporal delay,
and provides structured recovery actions.
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from app.modules.observation.visual_reasoning import VisualReasoningEngine

logger = logging.getLogger("nova.observer")

@dataclass
class Observation:
    """Outcome of observing an action's environmental results."""
    success: bool
    confidence: float                  # Score between 0.0 and 1.0
    state: str                         # "completed", "partial", "failed", "unknown"
    evidence: List[str] = field(default_factory=list)
    error: Optional[str] = None
    suggestion: Optional[str] = None
    recovery_hints: List[str] = field(default_factory=list)
    anomaly_detected: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "confidence": self.confidence,
            "state": self.state,
            "evidence": self.evidence,
            "error": self.error,
            "suggestion": self.suggestion,
            "recovery_hints": self.recovery_hints,
            "anomaly_detected": self.anomaly_detected
        }


class ObservationEngine:
    """
    Decentralized Environmental Observation Engine.
    Performs multi-layered verification: DOM, System, and Visual checks.
    """

    def __init__(self):
        # Generic primitives for DOM checking (case-insensitive checks)
        self.success_primitives = ["success", "sent", "saved", "completed", "done", "uploaded", "created", "active", "submitted"]
        self.error_primitives = ["error", "failed", "unauthorized", "expired", "timed out", "bad request", "invalid", "denied", "incorrect"]
        self.loader_primitives = ["loading", "spinner", "wait", "processing", "uploading", "progress"]
        self.anomaly_primitives = ["captcha", "robot", "verify you are human", "suspicious activity", "access denied", "blocked"]
        self.visual_engine = VisualReasoningEngine()

    async def observe_tool_result(self, tool_name: str, result: dict, state: Any = None) -> Observation:
        """
        Main observation entry point. Analyzes tool outcome and the active environment.
        """
        success = result.get("success", False)
        error_msg = result.get("error", "")
        output = result.get("output", "")
        
        evidence = []
        recovery_hints = []
        anomaly_detected = False
        confidence = 0.5
        state_str = "unknown"

        # ── 1. Safe Browser Environment Check ────────────────
        browser_page = None
        try:
            from app.modules.agent.tools.browser_tools import _get_browser
            # Check if browser is initialized without forcing a start
            from app.modules.agent.tools.browser_tools import _browser_ctrl
            if _browser_ctrl and _browser_ctrl._initialized:
                browser_page = await _browser_ctrl._ensure_page()
        except Exception as e:
            logger.debug(f"Browser check skipped: {e}")

        # ── 2. Handle Browser Specific Tools ─────────────────
        if browser_page and tool_name.startswith("browser_"):
            return await self._observe_browser_action(tool_name, success, error_msg, browser_page, state)

        # ── 3. Handle Filesystem/System Verification (Layer 3: Behavioral) ────
        if tool_name.startswith("fs_") or tool_name.startswith("file_") or tool_name == "create_note":
            return self._observe_system_action(tool_name, success, error_msg, result, state)

        # ── 4. Fallback: Standard Heuristic Evaluation ───────
        if success:
            state_str = "completed"
            confidence = 0.9 if output else 0.7
            evidence.append(f"Tool '{tool_name}' reported raw success")
            if output:
                evidence.append(f"Output received: {str(output)[:150]}")
        else:
            state_str = "failed"
            confidence = 0.95
            evidence.append(f"Tool '{tool_name}' reported direct failure: {error_msg}")
            recovery_hints = self._get_recovery_hints(tool_name, error_msg)

        suggestion = self._suggest_recovery(tool_name, error_msg, recovery_hints)
        
        # Sync simple milestones to state
        if state:
            if success:
                state.set_milestone(f"{tool_name}_executed", True)
            else:
                state.set_variable("last_execution_error", error_msg)

        return Observation(
            success=success,
            confidence=confidence,
            state=state_str,
            evidence=evidence,
            error=error_msg,
            suggestion=suggestion,
            recovery_hints=recovery_hints,
            anomaly_detected=anomaly_detected
        )

    async def _observe_browser_action(self, tool_name: str, tool_success: bool, tool_error: str, page, state: Any = None) -> Observation:
        """
        Layer 1 & 2 verification inside the active Playwright Browser.
        Performs temporal progressive polling to check for DOM changes.
        """
        evidence = []
        recovery_hints = []
        anomaly_detected = False
        
        # 1. Gather page metadata
        url = page.url
        title = await page.title()
        evidence.append(f"Active browser URL: {url}")
        evidence.append(f"Active browser title: {title}")

        # 2. Check for Instant Anomalies (Captchas, Blocks)
        body_text = (await page.inner_text("body")).lower()
        
        if any(p in body_text for p in self.anomaly_primitives) or "captcha" in url.lower():
            anomaly_detected = True
            evidence.append("Anomaly detected: CAPTCHA / Bot protection challenge is blocking the page!")
            recovery_hints.append("request_human_intervention")
            return Observation(
                success=False,
                confidence=0.98,
                state="failed",
                evidence=evidence,
                error="CAPTCHA_BLOCKED",
                suggestion="I encountered a security CAPTCHA screen. Please solve it on the browser window so I can resume.",
                recovery_hints=recovery_hints,
                anomaly_detected=True
            )

        # Detect Expired Session redirects
        if "login" in url.lower() and tool_name not in ["browser_open", "browser_type", "browser_click"] and "login" not in title.lower():
            evidence.append("Anomaly detected: Suddenly redirected to login page during an active session")
            recovery_hints.extend(["open_login_page", "input_credentials"])
            return Observation(
                success=False,
                confidence=0.95,
                state="failed",
                evidence=evidence,
                error="LOGIN_EXPIRED",
                suggestion="The website session expired and redirected me to the login page. I need to log in again.",
                recovery_hints=recovery_hints,
                anomaly_detected=True
            )

        # 3. Check generic primitives inside the DOM
        has_errors = any(p in body_text for p in self.error_primitives)
        
        # 4. Temporal Progressive Polling for Success State / Upload Spinners
        loading_cleared = True
        success_toast_found = False
        
        # Poll up to 5 seconds (5 * 1s wait cycles)
        for cycle in range(5):
            body_text = (await page.inner_text("body")).lower()
            
            # Check for active loaders/spinners
            is_loading = any(p in body_text for p in self.loader_primitives)
            
            # Check for success toasts or confirmation keywords
            has_success_toast = any(p in body_text for p in self.success_primitives)
            
            if not is_loading:
                loading_cleared = True
                if has_success_toast:
                    success_toast_found = True
                    break
            else:
                loading_cleared = False
                evidence.append(f"Temporal Polling (Cycle {cycle + 1}): Spinner/loading indicator active in DOM")
                
            await asyncio.sleep(1.0)

        # 5. Score Confidence Based on Gathered Evidence
        score = 0.0
        
        # Heuristics based on tool success
        if tool_success:
            score += 0.3
            evidence.append("Playwright action completed without driver error")
        else:
            score -= 0.2
            evidence.append(f"Playwright driver threw error: {tool_error}")

        if loading_cleared:
            score += 0.3
            evidence.append("All dynamic loading states/spinners have cleared")
        else:
            score -= 0.1
            evidence.append("Warning: Page is still in a loading/processing state")

        if success_toast_found:
            score += 0.4
            evidence.append("DOM matches success primitives (e.g. toast notification, 'done', 'success')")
        elif not has_errors:
            score += 0.2
            evidence.append("No obvious error message primitives found in the DOM")

        if has_errors:
            score -= 0.4
            evidence.append("Error messages matching primitives detected in the active DOM")

        # Clamp confidence score
        confidence = max(0.0, min(1.0, round(score, 2)))
        success = confidence >= 0.5
        state_str = "completed" if success else "failed"

        # Construct specific browser recovery hints
        if not success:
            if "selector" in tool_error.lower() or "locator" in tool_error.lower():
                recovery_hints.extend(["extract_text_context", "try_alternative_selector"])
            else:
                recovery_hints.append("retry_with_delay")

        suggestion = self._suggest_recovery(tool_name, tool_error if tool_error else "DOM match failed", recovery_hints)

        # Sync outcomes back to Task State Engine
        if state:
            state.set_variable("current_url", url)
            state.set_variable("current_title", title)
            if tool_name == "browser_open":
                state.set_milestone("browser_opened", success)
            elif tool_name == "browser_upload":
                state.set_milestone("upload_completed", success)
            
            if not success:
                state.set_variable("browser_error", tool_error or "DOM verification failed")

        # Double-check failure visually using the VisualReasoningEngine
        if not success:
            try:
                screenshot_path = await self.visual_engine.capture_browser_screenshot(page)
                if screenshot_path:
                    vis_result = await self.visual_engine.detect_anomalies_visually(screenshot_path)
                    if vis_result.get("anomaly_detected"):
                        anomaly_detected = True
                        evidence.append(f"Visual audit verified failure: {vis_result.get('description')}")
                        recovery_hints.append("visual_anomaly_recovery")
                        
                        return Observation(
                            success=False,
                            confidence=0.99,
                            state="failed",
                            evidence=evidence,
                            error=vis_result.get("anomaly_type"),
                            suggestion=vis_result.get("suggested_action"),
                            recovery_hints=recovery_hints,
                            anomaly_detected=True
                        )
            except Exception as e:
                logger.debug(f"Visual verification check skipped: {e}")

        return Observation(
            success=success,
            confidence=confidence,
            state=state_str,
            evidence=evidence,
            error=tool_error if not success else None,
            suggestion=suggestion,
            recovery_hints=recovery_hints,
            anomaly_detected=anomaly_detected
        )

    def _observe_system_action(self, tool_name: str, tool_success: bool, tool_error: str, result: dict, state: Any = None) -> Observation:
        """
        Layer 3: Behavioral Verification for OS / System actions.
        Physically verifies if requested files/directories/changes exists on disk.
        """
        evidence = []
        recovery_hints = []
        success = tool_success
        confidence = 0.5
        
        # Extract files paths if present in output/parameters
        path_str = ""
        output = result.get("output", "")
        
        # Look for paths in output string
        if isinstance(output, str) and ":" in output:
            for part in output.split():
                if "\\" in part or "/" in part:
                    path_str = part.strip("'\".,")
                    break

        # Check path existence physically on user's system
        if path_str:
            try:
                path = Path(path_str)
                if path.exists():
                    evidence.append(f"Behavioral Check: Confirmed file/folder physically exists: {path_str}")
                    evidence.append(f"File Size: {path.stat().st_size if path.is_file() else 'Directory'} bytes")
                    evidence.append(f"Last Modified: {time.ctime(path.stat().st_mtime)}")
                    success = True
                    confidence = 0.98
                else:
                    evidence.append(f"Behavioral Warning: File path returned by tool was NOT found on disk: {path_str}")
                    success = False
                    confidence = 0.95
                    tool_error = "FILE_NOT_FOUND_ON_DISK"
                    recovery_hints.append("verify_file_path")
            except Exception as e:
                logger.debug(f"Behavioral check failed: {e}")

        # Core logic if path was not explicitly found
        if not path_str:
            if tool_success:
                confidence = 0.8
                evidence.append("Tool finished execution successfully but behavioral verification was not applicable")
            else:
                confidence = 0.9
                evidence.append(f"Tool failed with error: {tool_error}")
                recovery_hints.append("verify_arguments")

        state_str = "completed" if success else "failed"
        suggestion = self._suggest_recovery(tool_name, tool_error, recovery_hints)

        # Sync state
        if state:
            if tool_name == "fs_index_search" and success:
                state.set_milestone("resource_selected", True)
            if not success:
                state.set_variable("system_error", tool_error)

        return Observation(
            success=success,
            confidence=confidence,
            state=state_str,
            evidence=evidence,
            error=tool_error if not success else None,
            suggestion=suggestion,
            recovery_hints=recovery_hints,
            anomaly_detected=False
        )

    def _get_recovery_hints(self, tool_name: str, error: str) -> List[str]:
        """Classify errors and return structured recovery actions."""
        err = (error or "").lower()
        hints = []

        if "permission" in err or "access" in err:
            hints.append("request_elevated_permissions")
        elif "timeout" in err:
            hints.extend(["retry_with_longer_timeout", "verify_process_responsive"])
        elif "not found" in err or "no such" in err:
            if "browser" in tool_name:
                hints.extend(["extract_text_context", "try_alternative_selector"])
            else:
                hints.extend(["verify_file_path", "run_filesystem_search"])
        elif "connection" in err or "network" in err or "offline" in err:
            hints.extend(["check_network_connection", "retry_with_delay"])
            
        return hints

    def _suggest_recovery(self, tool_name: str, error: str = None, hints: List[str] = None) -> str:
        """Generate a human-readable recovery suggestions using structured hints."""
        if not error:
            return "Task completed successfully."
            
        err = (error or "").lower()
        hints = hints or []

        if "request_human_intervention" in hints:
            return "Please solve the security check/CAPTCHA on the screen so I can continue."
            
        if "open_login_page" in hints:
            return "The website session has expired. I need to open the login page and re-authenticate."

        if "request_elevated_permissions" in hints:
            return "This operation requires administrator privileges. Please run the NOVA backend console as Admin."

        if "verify_file_path" in hints:
            return "I couldn't find the file on disk. Let me run a persistent index search to find where it is."

        if "extract_text_context" in hints:
            return "I couldn't locate the HTML element. Let me extract the full page context to find the correct selector."

        # Generic fallbacks
        if "timeout" in err:
            return "The operation timed out. I will try running it again with an increased delay."

        return "I will attempt an alternative planning path to accomplish this step."

    def observe_step_sequence(self, step_results: list[dict]) -> Observation:
        """
        Observe the outcome of a multi-step sequence.
        Determines overall achievement of goal.
        """
        if not step_results:
            return Observation(success=False, confidence=0.5, state="unknown",
                               evidence=["No steps were recorded in history"])

        total = len(step_results)
        successes = sum(1 for r in step_results if r.get("success", False))
        failures = total - successes

        evidence = [f"{successes} of {total} total steps completed successfully"]

        if successes == total:
            return Observation(
                success=True,
                confidence=0.98,
                state="completed",
                evidence=evidence
            )

        if successes > 0:
            return Observation(
                success=False,
                confidence=0.8,
                state="partial",
                evidence=evidence,
                suggestion="I succeeded on early steps, but hit an obstacle later. I will attempt to replan and complete the remaining steps."
            )

        return Observation(
            success=False,
            confidence=0.95,
            state="failed",
            evidence=evidence,
            suggestion="All actions failed. I need to formulate a completely different approach to reach the goal."
        )

    def should_retry(self, observation: Observation, attempt: int, max_attempts: int = 3) -> bool:
        """Determine if a step should be retried."""
        if observation.success:
            return False
        if attempt >= max_attempts:
            return False
            
        # Do not retry fatal issues
        if "request_human_intervention" in observation.recovery_hints:
            return False
        if "request_elevated_permissions" in observation.recovery_hints:
            return False
            
        return True

    def should_replan(self, observation: Observation) -> bool:
        """Determine if the orchestrator should trigger replanning."""
        if observation.state in ["failed", "partial"] and observation.confidence > 0.6:
            return True
        return False
