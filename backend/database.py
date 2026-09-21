import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from config import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enforce SQLite enterprise pragmas
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS tbl_sessions (
                session_id TEXT PRIMARY KEY,
                mission_profile TEXT NOT NULL,
                operator_persona TEXT,
                language TEXT DEFAULT 'en-US',
                created_at INTEGER NOT NULL,
                closed_at INTEGER,
                metadata_json TEXT
            );

            CREATE TABLE IF NOT EXISTS tbl_transcripts (
                segment_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sequence_index INTEGER NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                speaker TEXT NOT NULL,
                is_final INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 1.0,
                text TEXT NOT NULL,
                intent_class TEXT,
                FOREIGN KEY (session_id) REFERENCES tbl_sessions(session_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tbl_reasoning_traces (
                trace_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                query TEXT NOT NULL,
                retrieved_chunks TEXT,
                suggested_summary TEXT,
                bullet_points_json TEXT,
                code_snippet TEXT,
                confidence_score REAL,
                latency_ms INTEGER,
                FOREIGN KEY (session_id) REFERENCES tbl_sessions(session_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tbl_knowledge_docs (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tbl_autotype_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp_ms INTEGER NOT NULL,
                character_count INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                target_window_title TEXT,
                error_injected_count INTEGER DEFAULT 0
            );
            """)

    def save_session(self, session_id: str, profile: str, persona: str, language: str = "en-US"):
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO tbl_sessions (session_id, mission_profile, operator_persona, language, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (session_id, profile, persona, language, int(time.time() * 1000)))

    def append_transcript(self, session_id: str, segment: dict):
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO tbl_transcripts 
            (segment_id, session_id, sequence_index, timestamp_ms, speaker, is_final, confidence_score, text, intent_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                segment.get("segment_id"),
                session_id,
                segment.get("sequence_index", 0),
                segment.get("timestamp_ms", int(time.time() * 1000)),
                segment.get("speaker", "INTERVIEWER"),
                1 if segment.get("is_final") else 0,
                segment.get("confidence_score", 1.0),
                segment.get("text", ""),
                segment.get("intent_class")
            ))

    def save_reasoning_trace(self, session_id: str, trace_id: str, query: str, chunks: List[str],
                             summary: str, bullets: List[str], code: Optional[str],
                             confidence: float, latency_ms: int):
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO tbl_reasoning_traces 
            (trace_id, session_id, timestamp_ms, query, retrieved_chunks, suggested_summary, bullet_points_json, code_snippet, confidence_score, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace_id,
                session_id,
                int(time.time() * 1000),
                query,
                json.dumps(chunks),
                summary,
                json.dumps(bullets),
                code or "",
                confidence,
                latency_ms
            ))

    def save_document(self, doc_id: str, title: str, content: str, doc_type: str, sha256_hash: str):
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO tbl_knowledge_docs (doc_id, title, content, doc_type, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, title, content, doc_type, sha256_hash, int(time.time() * 1000)))

    def list_documents(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT doc_id, title, doc_type, sha256, created_at FROM tbl_knowledge_docs ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_all_document_contents(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT doc_id, title, content, doc_type FROM tbl_knowledge_docs")
            return [dict(row) for row in cur.fetchall()]

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            session = conn.execute("SELECT * FROM tbl_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not session:
                return {}
            transcripts = conn.execute(
                "SELECT * FROM tbl_transcripts WHERE session_id = ? ORDER BY timestamp_ms ASC", 
                (session_id,)
            ).fetchall()
            traces = conn.execute(
                "SELECT * FROM tbl_reasoning_traces WHERE session_id = ? ORDER BY timestamp_ms ASC", 
                (session_id,)
            ).fetchall()
            return {
                "session": dict(session),
                "transcripts": [dict(t) for t in transcripts],
                "reasoning_traces": [dict(tr) for tr in traces]
            }

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT session_id, mission_profile, operator_persona, created_at, closed_at FROM tbl_sessions ORDER BY created_at DESC LIMIT 50")
            return [dict(row) for row in cur.fetchall()]

db = Database()
