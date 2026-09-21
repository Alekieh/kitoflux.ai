"""
Conversational Execution Specification (CES) for KITOFLUX.AI.
The single source of truth defining session state, rolling transcript, and agent coordination.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time
import uuid

class MissionState(str, Enum):
    INITIALIZED = "INITIALIZED"
    LISTENING = "LISTENING"
    REASONING = "REASONING"
    INJECTING = "INJECTING"
    ARCHIVED = "ARCHIVED"

class Speaker(str, Enum):
    INTERVIEWER = "INTERVIEWER"
    CANDIDATE = "CANDIDATE"
    SYSTEM = "SYSTEM"

class TranscriptSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: f"seg_{uuid.uuid4().hex[:12]}")
    sequence_index: int = 0
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    speaker: Speaker = Speaker.INTERVIEWER
    is_final: bool = False
    confidence_score: float = 1.0
    text: str = ""
    intent_class: Optional[str] = None

class DocumentItem(BaseModel):
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    title: str
    content: str
    doc_type: str = "RESUME" # RESUME, JOB_DESCRIPTION, FAQ, RUNBOOK
    sha256: str
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))

class AgentState(BaseModel):
    agent_id: str
    role: str
    state: str = "IDLE" # IDLE, ACTIVE, BLOCKED, WAITING
    current_lease: int = 0
    scratchpad: Dict[str, Any] = Field(default_factory=dict)

class SessionContext(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mission_profile: str = "PROFILE_TECH_INTERVIEW"
    operator_persona: str = "Senior Full-Stack & Distributed Systems Architect"
    language: str = "en-US"
    max_latency_ms: int = 850
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))

class StrategicSuggestion(BaseModel):
    suggestion_id: str = Field(default_factory=lambda: f"sug_{uuid.uuid4().hex[:8]}")
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    query: str = ""
    summary: str = ""
    bullet_points: List[str] = Field(default_factory=list)
    code_snippet: Optional[str] = None
    confidence_score: float = 0.95
    citations: List[str] = Field(default_factory=list)
    raw_response: str = ""

class ConversationalExecutionSpec(BaseModel):
    context: SessionContext = Field(default_factory=SessionContext)
    state: MissionState = MissionState.INITIALIZED
    documents: List[DocumentItem] = Field(default_factory=list)
    transcript_buffer: List[TranscriptSegment] = Field(default_factory=list)
    current_suggestion: Optional[StrategicSuggestion] = None
    agent_matrix: Dict[str, AgentState] = Field(default_factory=dict)
    active_lease: int = 1
