"""
NOVA AI 2.0 — Resource Resolver
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decision intelligence engine for file selection.
Evaluates search candidates using heuristics (recency, semantic score)
and LLM intelligence to pick the absolute best target.
"""

import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class ResourceResolver:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def _get_intent_extension_boost(self, query: str, extension: str) -> float:
        """Boost specific file extensions based on detected intent in the query."""
        q = query.lower()
        ext = extension.lower().strip('.')
        
        # Read intents
        if any(w in q for w in ["read", "view", "show", "open document", "assignment", "report", "pdf", "summarize", "summary"]):
            if ext in ["pdf", "docx", "txt", "md"]: return 0.15
        
        # Edit/Code intents
        if any(w in q for w in ["edit", "code", "modify", "script", "program"]):
            if ext in ["py", "js", "html", "css", "cpp", "txt"]: return 0.15
            
        # Media intents
        if any(w in q for w in ["play", "listen", "watch", "image", "photo", "picture"]):
            if ext in ["mp3", "mp4", "png", "jpg", "jpeg", "wav"]: return 0.15
            
        return 0.0

    def _get_recency_boost(self, modified_at: float) -> float:
        """Boost recently modified files."""
        if not modified_at: return 0.0
        
        now = time.time()
        age_seconds = now - modified_at
        
        if age_seconds < 86400:          # < 1 day old
            return 0.20
        elif age_seconds < 604800:       # < 1 week old
            return 0.10
        elif age_seconds < 2592000:      # < 1 month old
            return 0.05
        
        return 0.0

    def _call_llm_tiebreaker(self, query: str, top_candidates: list[dict]) -> str:
        """Ask Groq to pick the best file path from the top contenders."""
        try:
            # Prepare candidates string
            candidates_json = json.dumps([
                {
                    "path": c["path"],
                    "filename": c["filename"],
                    "modified_days_ago": round((time.time() - c.get("modified_at", time.time())) / 86400, 1)
                } for c in top_candidates
            ], indent=2)
            
            prompt = f"""
You are NOVA AI's Decision Intelligence Engine.
The user wants to: "{query}"

Here are the top file candidates found in the system:
{candidates_json}

Based on the filenames, extensions, and how recently they were modified, choose the ONE absolute best file path for this task.
Respond ONLY with a JSON object containing the chosen path and your reasoning. Do not output markdown code blocks.
Format:
{{"best_path": "C:\\path\\to\\file", "reasoning": "This is the most recent final version."}}
"""
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=200
            )
            
            result = json.loads(completion.choices[0].message.content)
            return result.get("best_path")
        except Exception as e:
            print(f"Resolver LLM Error: {e}")
            return None

    def resolve_best_file(self, query: str, candidates: list[dict]) -> dict:
        """
        Evaluate candidates and return the single best match.
        Modifies the candidates in-place to add 'resolver_score'.
        """
        if not candidates:
            return None
            
        if len(candidates) == 1:
            candidates[0]["resolver_score"] = 1.0
            return candidates[0]

        # 1. Apply Heuristics
        for c in candidates:
            base_score = c.get("final_score", c.get("similarity", 0.5))
            recency_boost = self._get_recency_boost(c.get("modified_at", 0))
            intent_boost = self._get_intent_extension_boost(query, c.get("extension", ""))
            
            # Simple keyword penalty for old versions
            name = c.get("filename", "").lower()
            penalty = -0.15 if "old" in name or "archive" in name or "backup" in name else 0.0
            bonus = 0.10 if "final" in name or "latest" in name else 0.0
            
            c["resolver_score"] = base_score + recency_boost + intent_boost + penalty + bonus
            
        # Sort by resolver_score descending
        candidates.sort(key=lambda x: x["resolver_score"], reverse=True)
        
        # 2. Check for close ties among the top 3
        top_candidates = candidates[:3]
        if len(top_candidates) > 1:
            score_diff = top_candidates[0]["resolver_score"] - top_candidates[1]["resolver_score"]
            
            # If the top two are within 0.15 points, use LLM tie-breaker
            if score_diff < 0.15:
                best_path = self._call_llm_tiebreaker(query, top_candidates)
                if best_path:
                    # Find the candidate that matches the chosen path
                    for c in top_candidates:
                        if c["path"] == best_path:
                            # Boost its score so it floats to the top
                            c["resolver_score"] += 1.0
                            candidates.sort(key=lambda x: x["resolver_score"], reverse=True)
                            return c
                            
        return candidates[0]
