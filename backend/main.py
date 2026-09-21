import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from config import config
from kernel import kernel
from ces import MissionState

app = FastAPI(title="KITOFLUX.AI Core Kernel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartSessionRequest(BaseModel):
    mission_profile: str = "PROFILE_TECH_INTERVIEW"
    operator_persona: str = "Senior Distributed Systems Engineer"

class TranscriptEventRequest(BaseModel):
    text: str
    is_final: bool = True
    speaker: str = "INTERVIEWER"

class ReasoningRequest(BaseModel):
    query: str

class AutotypeRequest(BaseModel):
    text: Optional[str] = None

class KnowledgeUploadRequest(BaseModel):
    title: str
    content: str
    doc_type: str = "RESUME" # RESUME, JOB_DESCRIPTION, FAQ

class SettingsUpdateRequest(BaseModel):
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    typing_wpm: Optional[int] = None

@app.get("/api/health")
def health():
    return {
        "status": "RUNNING",
        "service": "KITOFLUX.AI Kernel",
        "mission_state": kernel.ces.state,
        "active_session": kernel.ces.context.session_id,
        "ws_clients_count": len(kernel.ws_clients)
    }

@app.post("/api/session/start")
def start_session(req: StartSessionRequest):
    kernel.start_session(profile=req.mission_profile, persona=req.operator_persona)
    return {"status": "SUCCESS", "session_id": kernel.ces.context.session_id}

@app.post("/api/session/stop")
def stop_session():
    kernel.stop_session()
    return {"status": "SUCCESS", "message": "Mission archived."}

@app.post("/api/transcript/event")
def transcript_event(req: TranscriptEventRequest):
    kernel.listener.ingest_transcript_event(text=req.text, is_final=req.is_final, speaker=req.speaker)
    return {"status": "RECEIVED"}

@app.post("/api/reason")
def trigger_reason(req: ReasoningRequest):
    kernel.schedule_reasoning(req.query)
    return {"status": "REASONING_SCHEDULED"}

@app.post("/api/autotype/trigger")
def trigger_autotype(req: AutotypeRequest):
    kernel.trigger_autotype(custom_text=req.text)
    return {"status": "AUTOTYPE_SCHEDULED"}

@app.post("/api/autotype/abort")
def abort_autotype():
    kernel.abort_autotype()
    return {"status": "ABORTED"}

@app.post("/api/knowledge/upload")
def upload_knowledge(req: KnowledgeUploadRequest):
    doc_id = kernel.add_knowledge_document(title=req.title, content=req.content, doc_type=req.doc_type)
    return {"status": "SUCCESS", "doc_id": doc_id}

@app.get("/api/knowledge")
def list_knowledge():
    return {"documents": kernel.db.list_documents()}

@app.get("/api/sessions")
def list_sessions():
    return {"sessions": kernel.db.list_sessions()}

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    history = kernel.db.get_session_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found")
    return history

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    if req.groq_api_key is not None:
        config.GROQ_API_KEY = req.groq_api_key
        kernel.strategist = kernel.strategist # refresh
    if req.openai_api_key is not None:
        config.OPENAI_API_KEY = req.openai_api_key
    if req.llm_provider is not None:
        config.LLM_PROVIDER = req.llm_provider
    if req.typing_wpm is not None:
        config.TYPING_WPM = req.typing_wpm
    return {"status": "SETTINGS_UPDATED"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    kernel.register_client(websocket)
    # Send initial state synchronization snapshot
    await websocket.send_json({
        "type": "INITIAL_SYNC",
        "state": kernel.ces.state,
        "session_id": kernel.ces.context.session_id,
        "persona": kernel.ces.context.operator_persona,
        "transcript_history": [s.model_dump() for s in kernel.ces.transcript_buffer[-15:]],
        "current_suggestion": kernel.ces.current_suggestion.model_dump() if kernel.ces.current_suggestion else None
    })
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "TRANSCRIPT_CHUNK":
                kernel.listener.ingest_transcript_event(
                    text=data.get("text", ""),
                    is_final=data.get("is_final", False),
                    speaker=data.get("speaker", "INTERVIEWER")
                )
            elif msg_type == "TRIGGER_AUTOTYPE":
                kernel.trigger_autotype(data.get("text"))
            elif msg_type == "ABORT_AUTOTYPE":
                kernel.abort_autotype()
            elif msg_type == "FORCE_REASON":
                kernel.schedule_reasoning(data.get("query", ""))
    except WebSocketDisconnect:
        kernel.unregister_client(websocket)
    except Exception:
        kernel.unregister_client(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False, log_level="info")
