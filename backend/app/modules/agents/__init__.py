"""
NOVA AI — Hierarchical Multi-Agent Coordination System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transitions NOVA from a single-agent autonomous platform to a
distributed cognitive architecture composed of specialized cooperating agents.
"""

from app.modules.agents.message_bus import AgentMessage, AgentMessageBus, SharedStateManager
from app.modules.agents.agent_base import BaseAgent
from app.modules.agents.delegation import TaskDelegationRouter, TemporaryDynamicAgent
from app.modules.agents.specialized_agents import (
    PlannerAgent,
    ExecutionAgent,
    VisionAgent,
    RecoveryAgent,
    MemoryAgent,
    ToolSynthesisAgent,
    ObservationAgent
)
