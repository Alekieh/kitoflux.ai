import time
import re
import asyncio
from typing import List, Dict, Any, Optional
from ces import StrategicSuggestion, MissionState
from knowledge.rag_engine import rag_engine
from drivers.llm_driver import llm_driver

class StrategistAgent:
    def __init__(self, kernel):
        self.kernel = kernel
        self.agent_id = "agent_strategist"
        self.role = "Context Synthesis & LLM Strategy"
        self.state = "IDLE"

    async def execute_turn_reasoning(self, query: str):
        self.state = "REASONING"
        self.kernel.ces.state = MissionState.REASONING
        self.kernel.broadcast_ws({"type": "MISSION_STATE", "state": MissionState.REASONING})

        start_time = time.time()
        
        # 1. Retrieve grounding chunks from local RAG
        matched_chunks = rag_engine.search(query, top_k=3)
        chunk_texts = [c["text"] for c in matched_chunks]
        citation_titles = list(set([c["title"] for c in matched_chunks]))

        # 2. Build tactical prompt
        persona = self.kernel.ces.context.operator_persona
        system_prompt = (
            f"You are the invisible real-time AI copilot for {persona}. "
            "Your output is displayed on an ultra-compact heads-up display during a live interview or call. "
            "Provide concise, high-impact tactical advice to help the operator answer flawlessly.\n"
            "Format your answer with:\n"
            "1. **Core Takeaway** (1 sentence summary)\n"
            "2. **Key Talking Points** (2-4 bullet points highlighting architectural concepts, metrics, and trade-offs)\n"
            "3. **Code / Concrete Example** (if technical/algorithmic, keep it short and clean)\n"
            "Ground your answer in the operator's background and provided context whenever possible."
        )

        full_response = ""
        suggestion_id = f"sug_{int(time.time()*1000)}"

        # Initial broadcast to notify UI that reasoning has begun
        self.kernel.broadcast_ws({
            "type": "REASONING_START",
            "suggestion_id": suggestion_id,
            "query": query,
            "citations": citation_titles
        })

        try:
            async for token in llm_driver.stream_reasoning(system_prompt, query, chunk_texts):
                full_response += token
                # Stream token chunk to HUD
                self.kernel.broadcast_ws({
                    "type": "REASONING_TOKEN",
                    "suggestion_id": suggestion_id,
                    "token": token
                })
        except Exception as e:
            full_response += f"\n[Inference Error: {str(e)}]"

        latency_ms = int((time.time() - start_time) * 1000)

        # Parse structured components
        bullets = self._extract_bullets(full_response)
        code_block = self._extract_code(full_response)
        confidence = 0.95 if matched_chunks else 0.88

        suggestion = StrategicSuggestion(
            suggestion_id=suggestion_id,
            timestamp_ms=int(time.time() * 1000),
            query=query,
            summary=self._extract_summary(full_response),
            bullet_points=bullets,
            code_snippet=code_block,
            confidence_score=confidence,
            citations=citation_titles,
            raw_response=full_response
        )

        self.kernel.ces.current_suggestion = suggestion

        # Persist to database
        self.kernel.db.save_reasoning_trace(
            session_id=self.kernel.ces.context.session_id,
            trace_id=suggestion_id,
            query=query,
            chunks=chunk_texts,
            summary=suggestion.summary,
            bullets=bullets,
            code=code_block,
            confidence=confidence,
            latency_ms=latency_ms
        )

        # Broadcast completed suggestion
        self.kernel.broadcast_ws({
            "type": "REASONING_COMPLETE",
            "suggestion": suggestion.model_dump(),
            "latency_ms": latency_ms
        })

        self.state = "IDLE"
        self.kernel.ces.state = MissionState.LISTENING
        self.kernel.broadcast_ws({"type": "MISSION_STATE", "state": MissionState.LISTENING})

    def _extract_summary(self, text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("*") and not line.startswith("-") and not line.startswith("#"):
                return re.sub(r"\*\*.*?\*\*:?", "", line).strip()
        return lines[0] if lines else "Tactical response prepared."

    def _extract_bullets(self, text: str) -> List[str]:
        bullets = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("* ") or stripped.startswith("- "):
                bullets.append(stripped[2:].strip())
        return bullets

    def _extract_code(self, text: str) -> Optional[str]:
        match = re.search(r"```(?:\w+)?\n([\s\S]*?)```", text)
        return match.group(1).strip() if match else None
