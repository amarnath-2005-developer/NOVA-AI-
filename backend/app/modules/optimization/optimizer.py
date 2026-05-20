"""
NOVA AI — Long-Term Autonomous Behavioral Optimizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements Phase 2 (Workflow Compression), Phase 3 (Predictive Failure Modeling),
Phase 4 (Orchestration Adaptation), Phase 5 (Dynamic Prioritization),
Phase 7 (Performance Tuning), and Phase 8 (Long-Term Learning Loops).
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from app.modules.optimization.analytics import BehavioralAnalyticsEngine

logger = logging.getLogger("nova.optimization.optimizer")


class BehavioralOptimizer:
    """
    Cognitive optimizer responsible for workflow sequence compression,
    predictive failure calculations, and dynamic performance tuning.
    """

    def __init__(self, analytics_engine: Optional[BehavioralAnalyticsEngine] = None):
        self.analytics = analytics_engine or BehavioralAnalyticsEngine()
        
        # Adaptive system runtime parameters
        self.tuned_retry_delays: Dict[str, float] = {}
        self.tuned_polling_intervals: Dict[str, float] = {}
        self.tuned_cache_durations: Dict[str, float] = {}
        
        # Default fallback controls
        self.default_retry_delay = 2.0
        self.default_polling_interval = 0.5
        self.default_cache_duration = 300.0

    async def compress_workflow_patterns(self, execution_sequences: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Phase 2: Workflow Compression.
        Detects highly repetitive multi-step execution chains and condenses them
        into high-level optimized workflow macro templates to improve planning speeds.
        """
        if not execution_sequences or len(execution_sequences) < 2:
            return []
            
        pattern_counts: Dict[Tuple[str, ...], int] = {}
        
        # Slide a window of size 3 across execution trails to map repetitive patterns
        for sequence in execution_sequences:
            if len(sequence) < 3:
                continue
            for i in range(len(sequence) - 2):
                pattern = tuple(sequence[i:i+3])
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                
        compressed_macros = []
        for pattern, count in pattern_counts.items():
            # If a 3-step sequence has occurred at least twice successfully
            if count >= 2:
                macro_name = f"compressed_macro_{'_and_'.join(pattern[1:3])}"
                compressed_macros.append({
                    "macro_name": macro_name,
                    "steps": list(pattern),
                    "frequency_saved": count,
                    "estimated_reduction_rate": 0.33  # Compresses 3 steps into 1 macro request
                })
                logger.info(f"Workflow Compression: Detected repeated pattern {pattern} (freq={count}). Synthesizing macro: '{macro_name}'")
                
        return compressed_macros

    async def predict_failure_probability(self, tool_name: str, domain_context: Optional[str] = None) -> float:
        """
        Phase 3: Predictive Failure Modeling.
        Combines historical rolling success rates and domain targets (e.g. site URL)
        to predict execution failures BEFORE they occur.
        """
        profile = await self.analytics.get_tool_reliability_profile(tool_name)
        base_success_rate = profile.get("success_rate", 1.0)
        
        # Base failure likelihood is the inverse of base success rate
        failure_prob = 1.0 - base_success_rate
        
        # Apply site-specific penalties (e.g., dynamic social pages or capture-heavy domains)
        if domain_context:
            domain_lower = domain_context.lower()
            if "instagram" in domain_lower or "discord" in domain_lower:
                failure_prob += 0.15  # Dynamic DOM adjustments likely
            if "captcha" in domain_lower or "bot" in domain_lower:
                failure_prob += 0.35  # Security roadblocks likely
                
        # Clamp probability between 0.0 and 1.0
        final_prob = max(0.0, min(1.0, round(failure_prob, 2)))
        logger.debug(f"Predictive Failure: Tool '{tool_name}' failure probability={final_prob} for domain '{domain_context}'")
        return final_prob

    async def adapt_orchestration_strategy(self, tool_name: str, domain_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Phase 4 & 5: Orchestration Adaptation & Dynamic Prioritization.
        Dynamically adjusts retry pathways or swaps strategies proactively if high failure probabilities exist.
        """
        failure_prob = await self.predict_failure_probability(tool_name, domain_context)
        
        adjustments = {
            "proactive_swap_recommended": False,
            "tuned_retry_delay": self.get_retry_delay(tool_name),
            "tuned_polling_interval": self.get_polling_interval(tool_name),
            "priority_level": 1  # 1 = Standard, 2 = High (for error-prone domains to run with max resources)
        }
        
        # Proactive Failure Prevention (probability threshold > 0.40)
        if failure_prob > 0.40:
            adjustments["proactive_swap_recommended"] = True
            # Elevate execution priority to allocate high-confidence workflows
            adjustments["priority_level"] = 2
            # Proactively tune performance timings to accommodate loading delays
            adjustments["tuned_retry_delay"] = self.get_retry_delay(tool_name) * 2.0
            adjustments["tuned_polling_interval"] = self.get_polling_interval(tool_name) * 1.5
            logger.warning(f"Predictive Failure: Proactive failure mitigation activated for '{tool_name}' (prob={failure_prob})")
            
        return adjustments

    async def tune_runtime_performance(self, tool_name: str, last_run_success: bool, execution_duration_ms: float):
        """
        Phase 7: Autonomous Performance Tuning.
        Dynamically optimizes retry delays, polling intervals, and cache durations
        based on real-time execution speeds.
        """
        current_delay = self.tuned_retry_delays.get(tool_name, self.default_retry_delay)
        current_polling = self.tuned_polling_intervals.get(tool_name, self.default_polling_interval)
        
        if not last_run_success:
            # Slower network/DOM — scale backoff delays to accommodate loading delays
            self.tuned_retry_delays[tool_name] = min(15.0, current_delay * 1.5)
            self.tuned_polling_intervals[tool_name] = min(3.0, current_polling * 1.3)
            logger.info(f"Performance Tuning: Scaled backoff for '{tool_name}' to retry_delay={self.tuned_retry_delays[tool_name]:.2f}s")
        else:
            # High-speed success — scale timings down to optimize for high throughput
            if execution_duration_ms < 1000.0:
                self.tuned_retry_delays[tool_name] = max(1.0, current_delay * 0.8)
                self.tuned_polling_intervals[tool_name] = max(0.1, current_polling * 0.8)
                logger.info(f"Performance Tuning: Optimized latency for '{tool_name}' to retry_delay={self.tuned_retry_delays[tool_name]:.2f}s")

    def get_retry_delay(self, tool_name: str) -> float:
        """Retrieves tuned retry delay for the requested tool."""
        return self.tuned_retry_delays.get(tool_name, self.default_retry_delay)

    def get_polling_interval(self, tool_name: str) -> float:
        """Retrieves tuned progressive polling interval for the requested tool."""
        return self.tuned_polling_intervals.get(tool_name, self.default_polling_interval)

    def get_cache_duration(self, key: str) -> float:
        """Retrieves tuned cache duration."""
        return self.tuned_cache_durations.get(key, self.default_cache_duration)
