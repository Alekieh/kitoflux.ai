import time
import re
from typing import Optional, Dict, Any
from ces import TranscriptSegment, Speaker, MissionState

class ListenerAgent:
    def __init__(self, kernel):
        self.kernel = kernel
        self.agent_id = "agent_listener"
        self.role = "Acoustic & Transcript Ingestion"
        self.state = "LISTENING"
        self.current_seq = 0

    def ingest_transcript_event(self, text: str, is_final: bool, speaker: str = "INTERVIEWER"):
        """
        Receives transcribed text from Web Speech API or local Whisper.
        Updates rolling transcript buffer and detects question boundaries.
        """
        text = text.strip()
        if not text:
            return

        self.current_seq += 1
        segment = TranscriptSegment(
            sequence_index=self.current_seq,
            timestamp_ms=int(time.time() * 1000),
            speaker=Speaker.INTERVIEWER if speaker.upper() == "INTERVIEWER" else Speaker.CANDIDATE,
            is_final=is_final,
            text=text,
            intent_class=self._classify_intent(text) if is_final else None
        )

        # Update CES
        self.kernel.ces.transcript_buffer.append(segment)
        if len(self.kernel.ces.transcript_buffer) > 30:
            self.kernel.ces.transcript_buffer.pop(0)

        # Persist to local database
        self.kernel.db.append_transcript(self.kernel.ces.context.session_id, segment.model_dump())

        # Broadcast to UI Channel 1
        self.kernel.broadcast_ws({
            "type": "TRANSCRIPT_UPDATE",
            "segment": segment.model_dump()
        })

        # Trigger Strategist if this is a finalized question/inquiry
        if is_final and segment.intent_class in ["QUESTION", "PROBLEM_STATEMENT", "TECHNICAL_CHALLENGE"]:
            self.kernel.schedule_reasoning(segment.text)

    def _classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        if text.endswith("?"):
            return "QUESTION"
        
        question_words = ["how", "what", "why", "when", "where", "can you", "could you", "tell me", "explain", "describe"]
        if any(text_lower.startswith(w) for w in question_words):
            return "QUESTION"

        if any(term in text_lower for term in ["architect", "design", "implement", "debug", "scale", "optimize"]):
            return "TECHNICAL_CHALLENGE"

        return "GENERAL_DIALOGUE"
