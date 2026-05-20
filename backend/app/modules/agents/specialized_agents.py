"""
NOVA AI — Specialized Distributed Agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Defines the concrete implementations of the 7 specialized distributed agents
performing Phase 6 & Phase 8 tasks, bridging core engines to the AgentMessageBus.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from app.modules.agents.agent_base import BaseAgent
from app.modules.agents.message_bus import AgentMessageBus, SharedStateManager

logger = logging.getLogger("nova.agents.specialized")


class PlannerAgent(BaseAgent):
    """
    Master Coordinating Agent (Phase 8 & Hierarchical Supervision).
    Manages workflow decomposition, task planning, subtask delegation, and supervision.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("planner_agent", bus, state_manager)
        self.register_capability("planning")
        
        # Core Engine Bridge
        from app.modules.agent.planner import TaskPlanner
        self.planner_engine = TaskPlanner()

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates or patches multi-step execution plans dynamically."""
        goal = task_payload.get("goal", "")
        context = task_payload.get("context", "")
        tools_schema = task_payload.get("tools_schema", "")
        
        logger.info(f"Planner Agent: Constructing topological plan for goal: '{goal}'")
        try:
            plan = await self.planner_engine.create_plan(
                goal=goal,
                tools_schema=tools_schema,
                context=context
            )
            return {"success": True, "plan": plan}
        except Exception as e:
            logger.error(f"Planner Agent: Failed to create plan: {e}")
            return {"success": False, "error": str(e)}


class ExecutionAgent(BaseAgent):
    """
    Tool Execution Specialist.
    Resolves dependencies, loads tools from registry, and runs actions safely.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("execution_agent", bus, state_manager)
        self.register_capability("execution")
        
        from app.modules.agent.tools.registry import register_all_tools
        self.registry = register_all_tools()

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Safely executes a tool action with evaluated variables."""
        tool_name = task_payload.get("tool_name", "")
        params = task_payload.get("parameters", {})
        
        logger.info(f"Execution Agent: Executing tool '{tool_name}'...")
        tool = self.registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found in registry"}
            
        try:
            result = await tool.safe_execute(**params)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Execution Agent: Tool '{tool_name}' failed: {e}")
            return {"success": False, "error": str(e)}


class VisionAgent(BaseAgent):
    """
    Multi-Modal Visual Reasoning Specialist (Phase 6).
    Performs visual OCR, screen segmentation, captcha detections, and pixel mapping.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("vision_agent", bus, state_manager)
        self.register_capability("vision")
        
        from app.modules.observation.visual_reasoning import VisualReasoningEngine
        self.vision_engine = VisualReasoningEngine()

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handles visual coordinate mapping or anomaly audits."""
        action = task_payload.get("action", "")
        image_path = task_payload.get("image_path", "")
        
        logger.info(f"Vision Agent: Performing visual operation: '{action}'")
        
        try:
            if action == "locate_element":
                desc = task_payload.get("element_description", "")
                coords = await self.vision_engine.locate_element_visually(desc, image_path)
                return {"success": coords is not None, "coordinates": coords}
                
            elif action == "detect_anomalies":
                anom = await self.vision_engine.detect_anomalies_visually(image_path)
                return {"success": True, "anomalies": anom}
                
            elif action == "segment_layout":
                layout = await self.vision_engine.analyze_layout_semantics(image_path)
                return {"success": True, "layout": layout}
                
            return {"success": False, "error": f"Unsupported vision action: '{action}'"}
        except Exception as e:
            logger.error(f"Vision Agent action failed: {e}")
            return {"success": False, "error": str(e)}


class RecoveryAgent(BaseAgent):
    """
    Self-Healing and Recovery Specialist.
    Resolves anomalies, patches dynamic schedules, and handles strategic escalations.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("recovery_agent", bus, state_manager)
        self.register_capability("recovery")
        
        # Set up recovery engine bridging the planner client
        from app.modules.agent.recovery_engine import RecoveryEngine
        from app.modules.agent.planner import TaskPlanner
        self.recovery_engine = RecoveryEngine(planner_client=TaskPlanner().client)

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes execution step failures to determine self-healing plans."""
        error_msg = task_payload.get("error_msg", "")
        tool_name = task_payload.get("tool_name", "")
        goal = task_payload.get("goal", "")
        step_number = task_payload.get("step_number", 0)
        
        logger.info(f"Recovery Agent: Evaluating self-healing for tool '{tool_name}' failure...")
        
        try:
            # We wrap variables in a mock TaskState format for compatibility
            from app.modules.agent.task_state import TaskStateEngine
            mock_state = TaskStateEngine(goal=goal)
            mock_state.set_variable("last_execution_error", error_msg)
            
            decision = await self.recovery_engine.analyze_and_recover(
                tool_name=tool_name,
                error_msg=error_msg,
                state=mock_state,
                step_number=step_number
            )
            return {"success": True, "decision": decision}
        except Exception as e:
            logger.error(f"Recovery Agent failed to analyze anomaly: {e}")
            return {"success": False, "error": str(e)}


class MemoryAgent(BaseAgent):
    """
    Epistemic & Procedural Memory Specialist.
    Retrieves workflow templates, writes memory trails, and synchronizes environments.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("memory_agent", bus, state_manager)
        self.register_capability("memory")
        
        from app.modules.memory.workflow_memory import WorkflowMemory
        from app.modules.memory.procedural_memory import ProceduralMemoryEngine
        from app.modules.agent.planner import TaskPlanner
        self.workflow_memory = WorkflowMemory()
        self.procedural_memory = ProceduralMemoryEngine(groq_client=TaskPlanner().client)

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches similar past runs or retrieves generalized workflow templates."""
        action = task_payload.get("action", "")
        goal = task_payload.get("goal", "")
        
        logger.info(f"Memory Agent: Performing procedural action: '{action}'")
        
        try:
            if action == "find_similar_workflows":
                runs = await self.workflow_memory.find_similar_workflows(goal)
                return {"success": True, "workflows": runs}
                
            elif action == "get_matching_procedure":
                proc = await self.procedural_memory.get_matching_procedure(goal)
                return {"success": True, "procedure": proc}
                
            return {"success": False, "error": f"Unsupported memory action: '{action}'"}
        except Exception as e:
            logger.error(f"Memory Agent action failed: {e}")
            return {"success": False, "error": str(e)}


class ToolSynthesisAgent(BaseAgent):
    """
    Generative Tool Synthesis Specialist.
    Generates new code assets, runs py_compile sandboxing, and handles promotions.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("tool_synthesis_agent", bus, state_manager)
        self.register_capability("tool_synthesis")
        
        from app.modules.agent.tools.dynamic_synthesis import DynamicToolSynthesisEngine
        from app.modules.agent.planner import TaskPlanner
        self.synthesis_engine = DynamicToolSynthesisEngine(groq_client=TaskPlanner().client)

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes code classes and registers them dynamic registry."""
        tool_name = task_payload.get("tool_name", "")
        objective = task_payload.get("objective", "")
        parameters = task_payload.get("parameters", {})
        
        logger.info(f"Tool Synthesis Agent: Generating custom tool '{tool_name}' on the fly...")
        
        try:
            tool_instance = await self.synthesis_engine.synthesize_and_register(
                tool_name=tool_name,
                objective=objective,
                parameters=parameters
            )
            return {"success": tool_instance is not None}
        except Exception as e:
            logger.error(f"Tool Synthesis Agent failed to synthesize tool: {e}")
            return {"success": False, "error": str(e)}


class ObservationAgent(BaseAgent):
    """
    Environmental Observation & Verification Specialist.
    Performs progressive DOM checks, gathers viewport titles, and checks status rules.
    """

    def __init__(self, bus: AgentMessageBus, state_manager: SharedStateManager):
        super().__init__("observation_agent", bus, state_manager)
        self.register_capability("observation")
        
        from app.modules.observation.observer import ObservationEngine
        self.observer_engine = ObservationEngine()

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates execution outputs post-step to double-check success evidence."""
        tool_name = task_payload.get("tool_name", "")
        result_dict = task_payload.get("result", {})
        goal = task_payload.get("goal", "")
        
        logger.info(f"Observation Agent: Performing post-action audit for tool '{tool_name}'...")
        
        try:
            from app.modules.agent.task_state import TaskStateEngine
            mock_state = TaskStateEngine(goal=goal)
            
            obs = await self.observer_engine.observe_tool_result(
                tool_name=tool_name,
                result=result_dict,
                state=mock_state
            )
            return {"success": True, "observation": obs.to_dict()}
        except Exception as e:
            logger.error(f"Observation Agent failed post-action audit: {e}")
            return {"success": False, "error": str(e)}
