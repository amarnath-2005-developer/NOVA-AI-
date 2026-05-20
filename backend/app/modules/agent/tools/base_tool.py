"""
NOVA AI 2.0 — Base Tool Abstraction
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abstract base class that ALL tools must implement.
Each tool is a self-contained, reusable capability unit.
The LLM planner discovers tools dynamically via their schemas.
"""

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass, field
import time


@dataclass
class ToolResult:
    """Standardized result from any tool execution."""
    success: bool
    output: Any = None
    error: str = None
    duration_ms: float = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    Abstract base class for all NOVA agent tools.
    
    Every tool must declare:
    - name: unique identifier (e.g. 'browser_open')
    - description: what this tool does (used by LLM planner)
    - parameters: dict of param_name → param_description
    - category: tool group (browser, filesystem, desktop, system, api)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for LLM planner."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        Parameter schema: { "param_name": "description" }
        Example: { "url": "The URL to open in the browser" }
        """
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        """Tool category: browser, filesystem, desktop, system, api"""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        Must return a ToolResult with success/failure status.
        """
        ...

    def get_schema(self) -> dict:
        """
        Returns the tool's schema in a format the LLM planner can consume.
        This is injected into the planner prompt so it knows what tools exist.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category
        }

    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Wrapper that catches exceptions and measures execution time.
        Always call this instead of execute() directly.
        """
        start = time.perf_counter()
        try:
            result = await self.execute(**kwargs)
            result.duration_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            return ToolResult(
                success=False,
                error=f"Tool '{self.name}' failed: {str(e)}",
                duration_ms=duration
            )

    def __repr__(self):
        return f"<Tool: {self.name} [{self.category}]>"
