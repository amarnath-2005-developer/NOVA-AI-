"""
NOVA AI — Agent Base Class
━━━━━━━━━━━━━━━━━━━━━━━━━━
Defines the abstract base model implementing Phase 2 standards.
All cooperative agents derive from this class to guarantee seamless async coordination.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Optional
from app.modules.agents.message_bus import AgentMessage, AgentMessageBus, SharedStateManager

logger = logging.getLogger("nova.agents.base")


class BaseAgent(ABC):
    """
    Abstract Base Class for all distributed specialized agents in the system.
    Supports asynchronous message routing, task delegation, event pub-sub, and shared state sync.
    """

    def __init__(self, agent_id: str, bus: AgentMessageBus, state_manager: SharedStateManager):
        self.agent_id = agent_id
        self.bus = bus
        self.state_manager = state_manager
        self.capabilities: List[str] = []
        self.status = "idle"  # idle, busy, suspended, error
        
        # Auto-subscribe agent to receive messages routed specifically to its ID
        self.bus.subscribe(f"agent.{self.agent_id}", self.receive_message)
        logger.info(f"Agent Base: Initialized agent '{self.agent_id}' and subscribed to topic 'agent.{self.agent_id}'")

    @property
    def name(self) -> str:
        """Returns the human-readable identifier of the agent."""
        return self.agent_id

    def register_capability(self, capability: str):
        """Declares that this agent specializes in a specific operation category."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            logger.debug(f"Agent '{self.agent_id}' registered capability: '{capability}'")

    async def publish_event(self, topic: str, payload: Dict[str, Any], priority: int = 1):
        """Broadcasts an event message asynchronously to all subscribed listeners."""
        msg = AgentMessage(
            sender=self.agent_id,
            receiver="*",  # Broadcast target
            topic=topic,
            payload=payload,
            priority=priority
        )
        await self.bus.publish(msg)
        logger.debug(f"Agent '{self.agent_id}' broadcasted event '{topic}'")

    async def request_subtask(self, target_agent: str, task_name: str,
                              payload: Dict[str, Any], priority: int = 1, timeout: float = 15.0) -> Dict[str, Any]:
        """
        Delegates a sub-task directly to another specialized agent and suspends execution
        until a completed response payload is returned.
        """
        logger.info(f"Agent '{self.agent_id}' delegating subtask '{task_name}' to '{target_agent}'")
        msg = AgentMessage(
            sender=self.agent_id,
            receiver=target_agent,
            topic=f"task.{task_name}",
            payload=payload,
            priority=priority
        )
        
        try:
            # Map request-response via message bus
            response = await self.bus.send_request(msg, timeout=timeout)
            return response.payload
        except Exception as e:
            logger.error(f"Agent '{self.agent_id}' delegation for subtask '{task_name}' failed: {e}")
            raise e

    async def update_state(self, key: str, value: Any):
        """Safely mutates variables in the SharedStateManager."""
        await self.state_manager.set(key, value, author=self.agent_id)

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Safely reads variables from the SharedStateManager."""
        return await self.state_manager.get(key, default)

    async def report_status(self) -> Dict[str, Any]:
        """Reports capabilities, operational status, and ID metrics."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "capabilities": self.capabilities,
            "type": self.__class__.__name__
        }

    @abstractmethod
    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary execution entry point. Each specialized agent overrides this method
        to deliver its core reasoning capability.
        """
        pass

    async def receive_message(self, message: AgentMessage):
        """
        Incoming routing target. Intercepts delegated tasks or event triggers,
        processes them, and returns results back if resolving a Request-Response.
        """
        logger.debug(f"Agent '{self.agent_id}' received message '{message.topic}' from '{message.sender}'")
        
        # Check if the message is a task request
        if message.topic.startswith("task."):
            self.status = "busy"
            try:
                result = await self.execute_task(message.payload)
                # Dispatch response back directly
                await self.bus.send_response(message, result, sender=self.agent_id)
            except Exception as e:
                logger.error(f"Agent '{self.agent_id}' failed executing task '{message.topic}': {e}")
                err_payload = {"success": False, "error": str(e)}
                await self.bus.send_response(message, err_payload, sender=self.agent_id)
            finally:
                self.status = "idle"
        else:
            # Event trigger or direct response — process internally
            await self.handle_internal_event(message)

    async def handle_internal_event(self, message: AgentMessage):
        """Optional hook. Overridden by agents to react to broadcasted system events asynchronously."""
        pass
