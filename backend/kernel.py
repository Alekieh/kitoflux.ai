import asyncio
import json
import uuid
import hashlib
from typing import Set, Dict, Any, Optional
from config import config
from ces import ConversationalExecutionSpec, SessionContext, MissionState, DocumentItem
from database import db
from knowledge.rag_engine import rag_engine
from agents.listener import ListenerAgent
from agents.strategist import StrategistAgent
from agents.executor import ExecutorAgent

class RuntimeKernel:
    def __init__(self):
        self.config = config
        self.db = db
        self.ces = ConversationalExecutionSpec()
        self.ws_clients: Set[Any] = set()
        
        # Instantiate Agents
        self.listener = ListenerAgent(self)
        self.strategist = StrategistAgent(self)
        self.executor = ExecutorAgent(self)
        
        # Active background tasks
        self.reasoning_task: Optional[asyncio.Task] = None
        self.autotype_task: Optional[asyncio.Task] = None
        
        # Load existing documents into in-memory RAG
        self._load_stored_documents()

    def _load_stored_documents(self):
        docs = self.db.get_all_document_contents()
        for doc in docs:
            rag_engine.ingest_document(
                doc_id=doc["doc_id"],
                title=doc["title"],
                content=doc["content"],
                doc_type=doc["doc_type"]
            )

    def register_client(self, websocket):
        self.ws_clients.add(websocket)

    def unregister_client(self, websocket):
        self.ws_clients.discard(websocket)

    def broadcast_ws(self, message: Dict[str, Any]):
        """Dispatches event to all connected HUD renderers asynchronously."""
        if not self.ws_clients:
            return
        payload = json.dumps(message)
        dead_clients = set()
        for ws in self.ws_clients:
            try:
                asyncio.create_task(ws.send_text(payload))
            except Exception:
                dead_clients.add(ws)
        self.ws_clients.difference_update(dead_clients)

    def start_session(self, profile: str = "PROFILE_TECH_INTERVIEW", persona: str = "Senior Systems Engineer"):
        session_id = str(uuid.uuid4())
        self.ces.context = SessionContext(
            session_id=session_id,
            mission_profile=profile,
            operator_persona=persona
        )
        self.ces.state = MissionState.LISTENING
        self.ces.transcript_buffer = []
        self.ces.current_suggestion = None

        self.db.save_session(session_id, profile, persona)
        
        self.broadcast_ws({
            "type": "SESSION_STARTED",
            "session_id": session_id,
            "profile": profile,
            "persona": persona
        })

    def stop_session(self):
        self.ces.state = MissionState.ARCHIVED
        self.broadcast_ws({
            "type": "SESSION_ARCHIVED",
            "session_id": self.ces.context.session_id
        })

    def schedule_reasoning(self, query: str):
        """Dispatches reasoning task without blocking the event loop."""
        if self.reasoning_task and not self.reasoning_task.done():
            self.reasoning_task.cancel()
        self.reasoning_task = asyncio.create_task(self.strategist.execute_turn_reasoning(query))

    def trigger_autotype(self, custom_text: Optional[str] = None):
        """Triggers the humanized autotyper."""
        if self.autotype_task and not self.autotype_task.done():
            self.executor.abort()
        self.autotype_task = asyncio.create_task(self.executor.execute_autotype(custom_text))

    def abort_autotype(self):
        self.executor.abort()

    def add_knowledge_document(self, title: str, content: str, doc_type: str = "RESUME") -> str:
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        self.db.save_document(doc_id, title, content, doc_type, sha256_hash)
        rag_engine.ingest_document(doc_id, title, content, doc_type)
        
        self.ces.documents.append(DocumentItem(
            doc_id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            sha256=sha256_hash
        ))

        self.broadcast_ws({
            "type": "KNOWLEDGE_UPDATED",
            "doc_id": doc_id,
            "title": title
        })
        return doc_id

kernel = RuntimeKernel()
