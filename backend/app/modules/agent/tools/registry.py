"""
NOVA AI 2.0 — Dynamic Tool Registry
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Central registry that discovers and manages all available tools.
The planner queries this registry to know what capabilities exist.
Tools register themselves automatically on import.
"""

from typing import Optional
from app.modules.agent.tools.base_tool import BaseTool


class ToolRegistry:
    """
    Singleton tool registry. All tools register here.
    The planner agent queries this to build its tool schema.
    """

    _instance: Optional["ToolRegistry"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if ToolRegistry._initialized:
            return
        self._tools: dict[str, BaseTool] = {}
        self._categories: dict[str, list[str]] = {}
        ToolRegistry._initialized = True

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance in the registry."""
        self._tools[tool.name] = tool
        cat = tool.category
        if cat not in self._categories:
            self._categories[cat] = []
        if tool.name not in self._categories[cat]:
            self._categories[cat].append(tool.name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_by_category(self, category: str) -> list[BaseTool]:
        """Get all tools in a category."""
        names = self._categories.get(category, [])
        return [self._tools[n] for n in names if n in self._tools]

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_categories(self) -> list[str]:
        """List all tool categories."""
        return list(self._categories.keys())

    def get_all_schemas(self) -> list[dict]:
        """
        Returns schemas for ALL registered tools.
        This is injected into the LLM planner prompt.
        Optimized: schemas are lightweight dicts, no heavy computation.
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def get_schemas_for_categories(self, categories: list[str]) -> list[dict]:
        """Get schemas for specific categories only (reduces prompt size)."""
        schemas = []
        for cat in categories:
            for tool in self.get_by_category(cat):
                schemas.append(tool.get_schema())
        return schemas

    def get_compact_tool_list(self) -> str:
        """
        Returns a compact string representation for LLM context.
        Minimizes token usage while preserving all info the planner needs.
        """
        lines = []
        for cat in sorted(self._categories.keys()):
            lines.append(f"\n[{cat.upper()}]")
            for name in self._categories[cat]:
                tool = self._tools[name]
                params = ", ".join(f"{k}" for k in tool.parameters.keys())
                lines.append(f"  • {name}({params}) — {tool.description}")
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return len(self._tools)


def get_registry() -> ToolRegistry:
    """Get the global tool registry singleton."""
    return ToolRegistry()


def register_all_tools() -> ToolRegistry:
    """
    Import and register all tool modules.
    Called once at startup to populate the registry.
    Uses lazy imports to minimize startup time.
    """
    registry = get_registry()

    # Only register if empty (idempotent)
    if registry.count > 0:
        return registry

    # Import tool modules — each module registers its tools on import
    from app.modules.agent.tools import system_tools
    from app.modules.agent.tools import filesystem_tools
    from app.modules.agent.tools import desktop_tools
    from app.modules.agent.tools import browser_tools
    from app.modules.agent.tools import api_tools

    return registry
