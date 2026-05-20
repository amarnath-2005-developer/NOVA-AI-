"""
NOVA AI 2.0 — Task State Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The working memory of the autonomous agent.
Maintains state, variables, and execution history across multi-step plans.
"""

import uuid
import time
from typing import Any, Dict, List

class TaskStateEngine:
    def __init__(self, goal: str, user_id: str):
        self.session_id = str(uuid.uuid4())
        self.goal = goal
        self.user_id = user_id
        
        self.current_step = 0
        self.total_steps = 0
        self.status = "in_progress"
        
        # Working memory
        self.variables: Dict[str, Any] = {}
        self.milestones: Dict[str, bool] = {}
        
        # Execution history
        self.execution_log: List[Dict] = []
        self.step_results: List[Dict] = []
        
        self.start_time = time.perf_counter()

    def set_variable(self, key: str, value: Any):
        """Store a variable in working memory."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Retrieve a variable from working memory."""
        return self.variables.get(key, default)
        
    def set_milestone(self, name: str, achieved: bool = True):
        """Track high-level achievements during execution."""
        self.milestones[name] = achieved

    def log_step(self, step_number: int, tool_name: str, params: dict, 
                 success: bool, output: Any, error: str, duration_ms: float):
        """Record the outcome of a step."""
        log_entry = {
            "step": step_number,
            "tool": tool_name,
            "parameters": params,
            "success": success,
            "output": str(output)[:300] if output else None,
            "error": error,
            "duration_ms": duration_ms
        }
        self.execution_log.append(log_entry)
        
        # Automatically extract variables from common tool outputs
        if success and isinstance(output, dict):
            # E.g. File Index Search returns {"best_match": {"path": "..."}}
            if "best_match" in output and isinstance(output["best_match"], dict):
                path = output["best_match"].get("path")
                if path:
                    self.set_variable("selected_resource_path", path)
                    self.set_milestone("resource_selected", True)

    def add_step_result(self, result_dict: dict):
        """Store raw tool result dict for observation."""
        self.step_results.append(result_dict)

    def advance_step(self):
        """Move to the next step."""
        self.current_step += 1

    def resolve_parameters(self, params: dict) -> dict:
        """
        Replace variable placeholders (e.g. '$state.selected_resource_path') 
        with actual values from working memory.
        """
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("$state."):
                var_name = v.replace("$state.", "")
                resolved[k] = self.get_variable(var_name, v) # Fallback to original string if not found
            elif isinstance(v, str) and "$state." in v:
                # Handle inline replacement like "C:/folder/$state.filename"
                new_v = v
                for var_key, var_val in self.variables.items():
                    placeholder = f"$state.{var_key}"
                    if placeholder in new_v:
                        new_v = new_v.replace(placeholder, str(var_val))
                resolved[k] = new_v
            else:
                resolved[k] = v
        return resolved

    def to_dict(self) -> dict:
        """Serialize state for LLM context or storage."""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "status": self.status,
            "progress": f"Step {self.current_step} of {self.total_steps}",
            "variables": self.variables,
            "milestones": self.milestones,
            "recent_history": self.execution_log[-3:] if self.execution_log else [],
            "duration_seconds": round(time.perf_counter() - self.start_time, 2)
        }
