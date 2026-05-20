"""
NOVA AI 2.0 — Agent Orchestrator (ReAct Reasoning Loop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The brain of the autonomous agent system.
Flow: Goal → Plan → Execute → Observe → Adapt → Complete

Replaces static if-else dispatching with dynamic reasoning.
Falls back gracefully to legacy pipeline on failure.
"""

import time
import logging
import asyncio
import json
from typing import Optional
from app.modules.agent.planner import TaskPlanner
from app.modules.agent.tools.registry import register_all_tools, get_registry
from app.modules.observation.observer import ObservationEngine
from app.modules.memory.workflow_memory import WorkflowMemory
from app.modules.agent.task_state import TaskStateEngine
from app.modules.agent.recovery_engine import RecoveryEngine
from app.modules.memory.procedural_memory import ProceduralMemoryEngine
from app.modules.agent.tools.dynamic_synthesis import DynamicToolSynthesisEngine
from app.modules.optimization import BehavioralAnalyticsEngine, BehavioralOptimizer
from app.modules.meta_cognition import MetaCognitiveAnalyzer, ArchitectureEvolver
from app.modules.agents import (
    AgentMessageBus,
    SharedStateManager,
    TaskDelegationRouter,
    PlannerAgent,
    ExecutionAgent,
    VisionAgent,
    RecoveryAgent as RecoveryAgentSpec,
    MemoryAgent,
    ToolSynthesisAgent,
    ObservationAgent
)

logger = logging.getLogger("nova.orchestrator")

# Constants for latency control
MAX_ITERATIONS = 10
MAX_RETRIES_PER_STEP = 2
STEP_TIMEOUT_SECONDS = 30


class AgentOrchestrator:
    """
    The core autonomous agent.
    Executes the ReAct loop: Plan → Execute → Observe → Adapt.
    """

    def __init__(self):
        self.planner = TaskPlanner()
        self.observer = ObservationEngine()
        self.workflow_memory = WorkflowMemory()
        self.recovery_engine = RecoveryEngine(planner_client=self.planner.client)
        self.procedural_memory = ProceduralMemoryEngine(groq_client=self.planner.client)
        self.tool_synthesis = DynamicToolSynthesisEngine(groq_client=self.planner.client)
        self._tools_initialized = False

        # Long-Term Autonomous Behavioral Optimization Engine
        self.analytics = BehavioralAnalyticsEngine()
        self.optimizer = BehavioralOptimizer(analytics_engine=self.analytics)

        # Self-Organizing Cognitive Architecture & Meta-Learning Engine
        self.metacog_analyzer = MetaCognitiveAnalyzer()
        self.arch_evolver = ArchitectureEvolver()

        # Asynchronous Inter-Agent Coordination Core
        self.bus = AgentMessageBus()
        self.state_manager = SharedStateManager()
        self.router = TaskDelegationRouter(bus=self.bus, state_manager=self.state_manager)

        # Instantiate specialized agents
        self.planner_agent = PlannerAgent(bus=self.bus, state_manager=self.state_manager)
        self.execution_agent = ExecutionAgent(bus=self.bus, state_manager=self.state_manager)
        self.vision_agent = VisionAgent(bus=self.bus, state_manager=self.state_manager)
        self.recovery_agent_spec = RecoveryAgentSpec(bus=self.bus, state_manager=self.state_manager)
        self.memory_agent = MemoryAgent(bus=self.bus, state_manager=self.state_manager)
        self.tool_synthesis_agent = ToolSynthesisAgent(bus=self.bus, state_manager=self.state_manager)
        self.observation_agent = ObservationAgent(bus=self.bus, state_manager=self.state_manager)

        # Register specialized agents
        self.router.register_agent(self.planner_agent)
        self.router.register_agent(self.execution_agent)
        self.router.register_agent(self.vision_agent)
        self.router.register_agent(self.recovery_agent_spec)
        self.router.register_agent(self.memory_agent)
        self.router.register_agent(self.tool_synthesis_agent)
        self.router.register_agent(self.observation_agent)

    def _ensure_tools(self):
        """Lazy-initialize tools on first use."""
        if not self._tools_initialized:
            register_all_tools()
            self._tools_initialized = True

    async def execute_goal(self, goal: str, user_id: str,
                           context: str = None) -> dict:
        """
        Main entry point: take a user goal and autonomously execute it.
        Wraps inter-agent bus async start/stop lifecycles safely around core.
        """
        await self.bus.start()
        try:
            return await self._execute_goal_core(goal, user_id, context)
        finally:
            await self.bus.stop()

    async def _execute_goal_core(self, goal: str, user_id: str,
                                 context: str = None) -> dict:
        start_time = time.perf_counter()

        self._ensure_tools()
        registry = get_registry()

        # Ensure Capability Graph default nodes are seeded and cached
        try:
            await self.planner.capability_graph.initialize_default_graph()
        except Exception as e:
            logger.warning(f"Failed to seed capability graph default nodes: {e}")

        # Ensure promoted dynamic tools are preloaded into active registry
        try:
            await self.tool_synthesis.load_promoted_tools()
        except Exception as e:
            logger.warning(f"Failed to preload promoted dynamic tools: {e}")

        # ── 1. Check workflow memory for similar past plans ────
        past_workflows = []
        try:
            past_workflows = await self.workflow_memory.find_similar_workflows(
                goal, user_id=user_id, limit=2)
        except Exception:
            pass  # Memory is optional, don't block execution

        # Check procedural memories for a matching generalized workflow template
        matching_proc = None
        try:
            matching_proc = await self.procedural_memory.get_matching_procedure(goal)
            if matching_proc:
                proc_context = (
                    f"\nHIGHLY SUCCESSFUL WORKFLOW TEMPLATE FOR THIS TASK (use this as guidance):\n"
                    f"Generalized Pattern: {matching_proc['task_pattern']}\n"
                    f"Steps:\n{json.dumps(matching_proc['steps'])}"
                )
                context = (context or "") + proc_context
        except Exception:
            pass

        # ── 2. Initialize Task State Engine ────────────────────────
        state = TaskStateEngine(goal=goal, user_id=user_id)
        self.recovery_engine.reset_recovery_history()

        # Fetch user profile to apply custom settings (model, temperature, etc.)
        from app.modules.user.user_manager import UserManager
        user_profile = await UserManager().load_user(user_id)

        # ── 3. Generate execution plan ─────────────────────────
        tools_schema = registry.get_compact_tool_list()
        plan = await self.planner.create_plan(
            goal=goal,
            tools_schema=tools_schema,
            context=context,
            past_workflows=past_workflows,
            user_profile=user_profile
        )

        plan_type = plan.get("type", "conversation")

        # ── Handle conversation responses (no action needed) ───
        if plan_type == "conversation":
            return {
                "intent": "CONVERSATION",
                "action": "agent_conversation",
                "message": plan.get("response", "I'm not sure how to help with that.")
            }

        # ── Handle clarification requests ──────────────────────
        if plan_type == "clarification":
            return {
                "intent": "CLARIFICATION",
                "action": "agent_clarify",
                "message": plan.get("question", "Could you provide more details?")
            }

        # ── Handle errors ──────────────────────────────────────
        if plan_type == "error":
            return {
                "intent": "ERROR",
                "action": "agent_error",
                "message": f"Planning failed: {plan.get('error', 'unknown error')}"
            }

        # ── 4. Execute action plan (ReAct loop) ───────────────
        steps = plan.get("steps", [])
        if not steps:
            return {
                "intent": "CONVERSATION",
                "action": "agent_empty_plan",
                "message": "I understood your request but couldn't determine the right actions."
            }

        state.total_steps = len(steps)
        replan_count = 0

        for iteration in range(MAX_ITERATIONS):
            if not steps:
                break

            state.advance_step()
            current_step = steps.pop(0)
            tool_name = current_step.get("tool", "")
            raw_params = current_step.get("parameters", {})
            
            # Resolve variables in parameters (e.g. $state.selected_resource_path)
            params = state.resolve_parameters(raw_params)

            # ── Get tool from registry ─────────────────────────
            tool = registry.get(tool_name)
            if not tool:
                logger.info(f"Orchestrator: Tool '{tool_name}' not found in registry. Invoking Dynamic Tool Synthesis...")
                try:
                    obj = current_step.get("expected_outcome", f"Execute dynamic custom tool logic for '{tool_name}'")
                    param_reqs = {k: "Dynamically mapped input parameter" for k in params.keys()}
                    tool = await self.tool_synthesis.synthesize_and_register(
                        tool_name=tool_name,
                        objective=obj,
                        parameters=param_reqs,
                        category="synthesized"
                    )
                except Exception as e:
                    logger.error(f"On-the-fly tool synthesis failed for '{tool_name}': {e}")

                if not tool:
                    # Tool not found and synthesis failed — log and skip
                    state.log_step(
                        step_number=current_step.get("step"),
                        tool_name=tool_name,
                        params=params,
                        success=False,
                        output=None,
                        error=f"Tool '{tool_name}' not found in registry and synthesis failed",
                        duration_ms=0
                    )
                    continue

            # ── Execute with retry logic ───────────────────────
            # ── Predictive Failure & Adaptation ─────────────────
            tuned_delay = self.optimizer.get_retry_delay(tool_name)
            tuned_timeout = STEP_TIMEOUT_SECONDS
            try:
                url = state.get_variable("current_url")
                adaptation = await self.optimizer.adapt_orchestration_strategy(tool_name, domain_context=url)
                tuned_delay = adaptation.get("tuned_retry_delay", tuned_delay)
                if adaptation.get("proactive_swap_recommended"):
                    logger.info(f"Orchestrator: Proactive fail-safe strategy triggered for tool '{tool_name}'! Tuning retry delay to {tuned_delay:.2f}s.")
            except Exception as e:
                logger.debug(f"Orchestrator adaptation check skipped: {e}")

            result = None
            for attempt in range(MAX_RETRIES_PER_STEP + 1):
                try:
                    result = await asyncio.wait_for(
                        tool.safe_execute(**params),
                        timeout=tuned_timeout
                    )
                except asyncio.TimeoutError:
                    result = type('ToolResult', (), {
                        'success': False,
                        'error': f"Step timed out after {tuned_timeout}s",
                        'output': None,
                        'duration_ms': tuned_timeout * 1000,
                        'to_dict': lambda self: {"success": False, "error": self.error}
                    })()

                # ── Observe result ─────────────────────────────
                result_dict = result.to_dict() if hasattr(result, 'to_dict') else {
                    "success": result.success, "output": result.output, "error": result.error}
                observation = await self.observer.observe_tool_result(tool_name, result_dict, state=state)

                # ── Record Telemetry & Tune Performance ─────────
                try:
                    dur = result.duration_ms if result else 0.0
                    success = observation.success
                    await self.analytics.record_execution_telemetry(
                        workflow_id=state.session_id,
                        tool_name=tool_name,
                        duration_ms=dur,
                        success=success,
                        retries=attempt,
                        coordination_overhead_ms=0.0
                    )
                    await self.optimizer.tune_runtime_performance(
                        tool_name=tool_name,
                        last_run_success=success,
                        execution_duration_ms=dur
                    )
                except Exception as e:
                    logger.debug(f"Telemetry recording failed: {e}")

                # Record recovery outcome if a recovery strategy was active
                rec_strat = state.get_variable("last_recovery_strategy")
                rec_class = state.get_variable("last_recovery_classification")
                if rec_strat and rec_class:
                    try:
                        await self.recovery_engine.record_recovery_outcome(rec_class, rec_strat, success=observation.success)
                    except Exception:
                        pass
                    # Clear strategy once recorded
                    state.set_variable("last_recovery_strategy", None)
                    state.set_variable("last_recovery_classification", None)

                if observation.success:
                    break  # Step succeeded

                # Check if retry is worthwhile
                if not self.observer.should_retry(observation, attempt, MAX_RETRIES_PER_STEP):
                    break

                logger.info(f"Retrying step {current_step.get('step')} (attempt {attempt + 2}) after {tuned_delay:.2f}s backoff")
                await asyncio.sleep(tuned_delay)

            # ── Log step result ────────────────────────────────
            state.add_step_result(result_dict)
            state.log_step(
                step_number=current_step.get("step"),
                tool_name=tool_name,
                params=params,
                success=observation.success,
                output=result.output if result else None,
                error=result.error if result else None,
                duration_ms=result.duration_ms if result else 0
            )

            # Record tool execution outcome in procedural memory
            try:
                await self.procedural_memory.record_tool_execution(tool_name, success=observation.success)
            except Exception:
                pass

            # Record dynamic tool execution stats
            try:
                await self.tool_synthesis.record_tool_execution(tool_name, success=observation.success)
            except Exception:
                pass

            # ── Handle failure: Recovery & Replanning Engine ───────────────
            if not observation.success:
                recovery_decision = await self.recovery_engine.analyze_and_recover(
                    tool_name=tool_name,
                    params=params,
                    observation=observation,
                    state=state,
                    step_queue=steps,
                    tools_schema=tools_schema
                )
                
                # Update state variables with recovery outcomes
                state.set_variable("last_recovery_strategy", recovery_decision.name)
                state.set_variable("last_recovery_message", recovery_decision.message)
                
                if recovery_decision.action == "retry_step":
                    if recovery_decision.patched_params:
                        current_step["parameters"] = recovery_decision.patched_params
                    # Re-queue step at the front
                    steps.insert(0, current_step)
                    state.current_step -= 1  # Decrement since it will be re-run
                    
                    logger.info(f"Recovery: Retrying step {current_step.get('step')} ({tool_name}) using strategy '{recovery_decision.name}'")
                    if recovery_decision.delay_seconds > 0:
                        logger.info(f"Recovery: Delaying {recovery_decision.delay_seconds}s before retry...")
                        await asyncio.sleep(recovery_decision.delay_seconds)
                    continue
                    
                elif recovery_decision.action == "inject_steps":
                    if recovery_decision.patched_params:
                        current_step["parameters"] = recovery_decision.patched_params
                    
                    # Prepend recovery steps and re-queue failed step
                    steps = recovery_decision.injected_steps + [current_step] + steps
                    state.total_steps = state.current_step + len(steps) - 1
                    state.current_step -= 1  # Decrement so it resets correctly on loop advance
                    
                    logger.info(f"Recovery: Injected {len(recovery_decision.injected_steps)} steps to resolve '{tool_name}' failure")
                    continue
                    
                elif recovery_decision.action == "replan":
                    replan_count += 1
                    logger.info(f"Recovery: Strategy '{recovery_decision.name}' triggered full LLM replanning...")
                    new_plan = await self.planner.replan(
                        original_goal=goal,
                        failed_step=current_step,
                        observation=observation.to_dict(),
                        tools_schema=tools_schema,
                        current_state=state.to_dict(),
                        user_profile=user_profile
                    )
                    if new_plan.get("type") == "action":
                        steps = new_plan.get("steps", [])
                        state.total_steps = state.current_step + len(steps)
                        continue

        # ── 5. Final observation ───────────────────────────────
        final_obs = self.observer.observe_step_sequence(state.step_results)
        state.status = "completed" if final_obs.success else "failed"
        total_duration = (time.perf_counter() - start_time) * 1000

        # ── 6. Store workflow in memory ────────────────────────
        try:
            await self.workflow_memory.store_workflow(
                user_id=user_id,
                goal=goal,
                plan=plan,
                steps_executed=state.execution_log,
                success=final_obs.success,
                duration_ms=total_duration
            )
            
            # Record successful generalized procedure
            if final_obs.success:
                await self.procedural_memory.record_successful_workflow(
                    goal=goal,
                    steps=state.execution_log,
                    duration_ms=total_duration
                )
        except Exception as e:
            logger.warning(f"Failed to store workflow: {e}")

        # ── 7. Build response message ──────────────────────────
        if final_obs.success:
            # Synthesize final response via LLM
            message = await self._synthesize_final_response(goal, state.execution_log)
            if not message:
                # Gather outputs from successful steps (fallback)
                outputs = [
                    log.get("output", "")
                    for log in state.execution_log
                    if log.get("success") and log.get("output")
                ]
                message = ". ".join(filter(None, outputs)) or plan.get("goal", "Task completed")
            intent = "AGENT_ACTION"
            action = "agent_complete"
        else:
            failed = [log for log in state.execution_log if not log.get("success")]
            error_msgs = [f.get("error", "Unknown error") for f in failed]
            message = f"I encountered issues: {'; '.join(error_msgs[:3])}"
            intent = "AGENT_PARTIAL" if any(l.get("success") for l in state.execution_log) else "AGENT_FAILED"
            action = "agent_partial" if intent == "AGENT_PARTIAL" else "agent_failed"

        # Generate behavioral heatmap
        try:
            await self.analytics.generate_behavioral_heatmap()
        except Exception as e:
            logger.debug(f"Failed to generate behavioral heatmap: {e}")

        # Meta-Cognitive Analysis & Architecture Evolution
        try:
            # Perform cognitive self-reflection
            await self.metacog_analyzer.perform_self_reflection()
            # Run cognitive health monitors
            health = await self.metacog_analyzer.monitor_cognitive_health()
            # Trigger autonomous architecture evolution loops
            if health.get("status") == "attention_needed":
                logger.info("Orchestrator: Cognitive health attention alert. Initiating dynamic architecture topology reorganization and capability consolidation...")
                await self.arch_evolver.evolve_architecture_topology()
        except Exception as e:
            logger.debug(f"Orchestrator meta-cognitive reflection skipped: {e}")

        # Collect any special metadata (like pdf_summary) from step results
        pdf_summary = None
        for res in state.step_results:
            if res.get("success") and isinstance(res.get("output"), dict):
                out = res.get("output")
                if "pdf_summary" in out:
                    pdf_summary = out["pdf_summary"]
                    break

        meta_dict = {
            "plan_type": plan_type,
            "steps_total": len(state.execution_log),
            "steps_succeeded": sum(1 for l in state.execution_log if l.get("success")),
            "duration_ms": round(total_duration, 2),
            "replanned": replan_count > 0
        }
        if pdf_summary:
            meta_dict["pdf_summary"] = pdf_summary

        return {
            "intent": intent,
            "action": action,
            "message": message,
            "metadata": meta_dict
        }

    async def _synthesize_final_response(self, goal: str, execution_log: list) -> str:
        """
        Use LLaMA to generate a clean, natural language response based on what was actually done.
        """
        try:
            # Format the steps for the LLM
            steps_summary = []
            for step in execution_log:
                status = "succeeded" if step.get("success") else "failed"
                tool = step.get("tool")
                output = step.get("output", "")
                # Clean up long outputs to save tokens
                output_str = str(output)[:200]
                steps_summary.append(f"- Step: {tool} ({status}) -> {output_str}")
            
            steps_formatted = "\n".join(steps_summary)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are NOVA AI, a highly advanced cybernetic assistant.\n"
                        "Your personality is professional, futuristic, and helpful.\n"
                        "Given the user's original goal and the list of executed steps, "
                        "generate a concise, natural response (1-2 sentences max) in your persona "
                        "confirming what was done. Avoid raw JSON, paths, or technical details."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"User Goal: {goal}\n"
                        f"Executed Steps:\n{steps_formatted}\n\n"
                        f"Response:"
                    )
                }
            ]

            loop = asyncio.get_running_loop()
            completion = await loop.run_in_executor(
                None,
                lambda: self.planner.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=150
                )
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to synthesize final response: {e}")
            return ""
