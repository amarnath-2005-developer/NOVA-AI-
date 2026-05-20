"""
NOVA AI — Task Delegation Router & Dynamic Spawning Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manages workflow routing, dependency resolution, parallel scheduling, and the
lifecycle of temporary, isolated sub-agents spawned for specialized operations.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from app.modules.agents.agent_base import BaseAgent
from app.modules.agents.message_bus import AgentMessageBus, SharedStateManager

logger = logging.getLogger("nova.agents.delegation")


class TemporaryDynamicAgent(BaseAgent):
    """Temporary dynamic runtime agent spawned to solve isolated subtasks."""

    def __init__(self, agent_id: str, bus: AgentMessageBus, state_manager: SharedStateManager,
                 custom_executor: Any):
        super().__init__(agent_id, bus, state_manager)
        self.custom_executor = custom_executor
        self.register_capability("dynamic_execution")

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the dynamically provided executor closure in an isolated context."""
        logger.info(f"Dynamic Agent '{self.agent_id}': Launching isolated execution context...")
        try:
            if asyncio.iscoroutinefunction(self.custom_executor):
                res = await self.custom_executor(task_payload, self)
            else:
                res = self.custom_executor(task_payload, self)
            return {"success": True, "output": res}
        except Exception as e:
            logger.error(f"Dynamic Agent '{self.agent_id}' execution failed: {e}")
            return {"success": False, "error": str(e)}


class TaskDelegationRouter:
    """
    Central router that directs workload routing, maps specialized capabilities,
    and manages the lifecycle of dynamically spawned temporary runtimes.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        self.bus = bus
        self.state_manager = state_manager
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.temporary_agents: Dict[str, TemporaryDynamicAgent] = {}

    def register_agent(self, agent: BaseAgent):
        """Adds a specialized agent to the routing directory."""
        self.registered_agents[agent.agent_id] = agent
        logger.info(f"Delegation Router: Registered agent '{agent.agent_id}' with capabilities {agent.capabilities}")

    def unregister_agent(self, agent_id: str):
        """Removes an agent from the router."""
        self.registered_agents.pop(agent_id, None)

    async def route_task(self, capability: str, task_payload: Dict[str, Any],
                         priority: int = 1, timeout: float = 20.0) -> Dict[str, Any]:
        """
        Locates the best specialized agent capable of executing the requested task
        and routes the execution payload over the Message Bus.
        """
        # Find best candidate agent specializing in this capability
        candidate = None
        for agent in self.registered_agents.values():
            if capability in agent.capabilities and agent.status == "idle":
                candidate = agent
                break
        
        # Fallback to any busy agent if no idle agents are found
        if not candidate:
            for agent in self.registered_agents.values():
                if capability in agent.capabilities:
                    candidate = agent
                    break
        
        if not candidate:
            logger.error(f"Delegation Router: No registered agent found with capability '{capability}'")
            return {"success": False, "error": f"NO_AGENT_CAPABILITY: {capability}"}
            
        logger.info(f"Delegation Router: Routing capability '{capability}' to agent '{candidate.agent_id}'")
        
        # Dispatch task through Message Bus
        try:
            # Reuses standard message delegation channels
            from app.modules.agents.message_bus import AgentMessage
            msg = AgentMessage(
                sender="delegation_router",
                receiver=candidate.agent_id,
                topic=f"task.{capability}",
                payload=task_payload,
                priority=priority
            )
            response = await self.bus.send_request(msg, timeout=timeout)
            return response.payload
        except Exception as e:
            logger.error(f"Delegation Router: Task execution routed to '{candidate.agent_id}' failed: {e}")
            return {"success": False, "error": f"ROUTING_EXECUTION_FAILURE: {str(e)}"}

    async def spawn_temporary_agent(self, prefix: str, custom_executor: Any) -> str:
        """
        Spawns a temporary isolated runtime sub-agent, registers it in the active bus
        and returns its unique dynamically generated ID.
        """
        import uuid
        agent_id = f"temp_{prefix}_{uuid.uuid4().hex[:6]}"
        
        temp_agent = TemporaryDynamicAgent(
            agent_id=agent_id,
            bus=self.bus,
            state_manager=self.state_manager,
            custom_executor=custom_executor
        )
        
        self.registered_agents[agent_id] = temp_agent
        self.temporary_agents[agent_id] = temp_agent
        logger.info(f"Delegation Router: Spawned temporary isolated agent '{agent_id}' successfully.")
        return agent_id

    async def terminate_temporary_agent(self, agent_id: str):
        """Cleans up resources, unsubscribes handlers, and terminates dynamic agent contexts."""
        if agent_id in self.temporary_agents:
            agent = self.temporary_agents.pop(agent_id)
            self.bus.unsubscribe(f"agent.{agent_id}", agent.receive_message)
            self.registered_agents.pop(agent_id, None)
            logger.info(f"Delegation Router: Terminated temporary agent '{agent_id}' cleanly and flushed contexts.")
        else:
            logger.warning(f"Delegation Router: Attempted to terminate invalid agent '{agent_id}'")

    async def execute_in_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes a sequence of independent agent sub-tasks in parallel using asyncio.gather
        to maximize speed.
        """
        async_tasks = []
        for task in tasks:
            capability = task.get("capability")
            payload = task.get("payload", {})
            priority = task.get("priority", 1)
            timeout = task.get("timeout", 20.0)
            
            if capability:
                async_tasks.append(
                    self.route_task(capability, payload, priority, timeout)
                )
                
        if not async_tasks:
            return []
            
        logger.info(f"Delegation Router: Executing {len(async_tasks)} tasks in parallel...")
        return list(await asyncio.gather(*async_tasks, return_exceptions=True))
