import sqlite3
import json
from datetime import datetime
from core.config import Config

class LiveAuditDatabase:
    """Active SQLite backend storing live verification audits and indexed public records."""

    def __init__(self, db_path: str = Config.SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claim_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    claim_text TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    explanation_en TEXT NOT NULL,
                    explanation_hi TEXT NOT NULL,
                    sub_claims_json TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    agent_trace_json TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    ela_score REAL NOT NULL,
                    authenticity_verdict TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    vision_analysis TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS live_documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_claim_audit(self, claim_text: str, result: dict):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO claim_audits (
                    created_at, claim_text, verdict, confidence,
                    explanation_en, explanation_hi, sub_claims_json,
                    sources_json, agent_trace_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat() + "Z",
                claim_text,
                result.get("verdict", "UNVERIFIED"),
                int(result.get("confidence", 50)),
                result.get("explanation_en", ""),
                result.get("explanation_hi", ""),
                json.dumps(result.get("sub_claims", [])),
                json.dumps(result.get("sources", [])),
                json.dumps(result.get("agent_trace", []))
            ))
            conn.commit()

    def save_media_audit(self, filename: str, sha256_hash: str, ela_score: float,
                         verdict: str, metadata: dict, vision_analysis: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO media_audits (
                    created_at, filename, sha256_hash, ela_score,
                    authenticity_verdict, metadata_json, vision_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat() + "Z",
                filename,
                sha256_hash,
                float(ela_score),
                verdict,
                json.dumps(metadata),
                vision_analysis
            ))
            conn.commit()

    def upsert_live_documents(self, docs: list):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat() + "Z"
            for d in docs:
                cursor.execute("""
                    INSERT OR REPLACE INTO live_documents (
                        doc_id, title, summary, url, source_name, published_at, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    d["doc_id"],
                    d["title"],
                    d["summary"],
                    d["url"],
                    d["source_name"],
                    d.get("published_at", now),
                    now
                ))
            conn.commit()

    def get_all_live_documents(self, limit: int = 250) -> list:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT doc_id, title, summary, url, source_name, published_at
                FROM live_documents
                ORDER BY fetched_at DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "doc_id": r[0], "title": r[1], "summary": r[2],
                    "url": r[3], "source_name": r[4], "published_at": r[5]
                }
                for r in rows
            ]

    def get_recent_claim_audits(self, limit: int = 25) -> list:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at, claim_text, verdict, confidence, explanation_en, sources_json
                FROM claim_audits ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0], "created_at": r[1], "claim_text": r[2],
                    "verdict": r[3], "confidence": r[4], "explanation_en": r[5],
                    "sources": json.loads(r[6])
                }
                for r in rows
            ]

    def get_recent_media_audits(self, limit: int = 15) -> list:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at, filename, sha256_hash, ela_score, authenticity_verdict, vision_analysis
                FROM media_audits ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0], "created_at": r[1], "filename": r[2],
                    "sha256_hash": r[3], "ela_score": r[4],
                    "authenticity_verdict": r[5], "vision_analysis": r[6]
                }
                for r in rows
            ]
