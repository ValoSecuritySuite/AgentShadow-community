"""SQLite-backed agent inventory.

Stores one row per discovered agent keyed by `agent_id`. Re-discovering an
agent upserts it (bumping `last_seen` + `scan_count`) so the inventory reflects
the current posture. Mirrors the persistence approach used by SaaSShadow's
`saas_map_store` / `scan_history`.
"""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas import Agent

logger = get_logger(__name__)

_lock = threading.Lock()
_initialized = False


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    db_path = Path(settings.inventory_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global _initialized
    with _lock:
        if _initialized:
            return
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    framework TEXT,
                    source TEXT,
                    owner TEXT,
                    discovery_path TEXT,
                    model TEXT,
                    autonomy_level TEXT,
                    risk_score REAL,
                    risk_level TEXT,
                    max_severity INTEGER,
                    posture_grade TEXT,
                    final_decision TEXT,
                    finding_count INTEGER,
                    tool_count INTEGER,
                    first_seen TEXT,
                    last_seen TEXT,
                    scan_count INTEGER,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def upsert_agent(agent: Agent) -> bool:
    """Insert or update an agent. Returns True when the agent is newly created."""
    init_db()
    with _lock:
        conn = _connect()
        try:
            existing = conn.execute(
                "SELECT first_seen, scan_count FROM agents WHERE agent_id = ?",
                (agent.agent_id,),
            ).fetchone()
            is_new = existing is None
            if existing is not None:
                agent.first_seen = _parse_dt(existing["first_seen"], agent.first_seen)
                agent.scan_count = int(existing["scan_count"] or 0) + 1
            conn.execute(
                """
                INSERT INTO agents (
                    agent_id, name, framework, source, owner, discovery_path, model,
                    autonomy_level, risk_score, risk_level, max_severity, posture_grade,
                    final_decision, finding_count, tool_count, first_seen, last_seen,
                    scan_count, payload
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    name=excluded.name, framework=excluded.framework, source=excluded.source,
                    owner=excluded.owner, discovery_path=excluded.discovery_path, model=excluded.model,
                    autonomy_level=excluded.autonomy_level, risk_score=excluded.risk_score,
                    risk_level=excluded.risk_level, max_severity=excluded.max_severity,
                    posture_grade=excluded.posture_grade, final_decision=excluded.final_decision,
                    finding_count=excluded.finding_count, tool_count=excluded.tool_count,
                    last_seen=excluded.last_seen, scan_count=excluded.scan_count,
                    payload=excluded.payload
                """,
                (
                    agent.agent_id, agent.name, agent.framework, agent.source, agent.owner,
                    agent.discovery_path, agent.model, agent.autonomy_level, agent.risk_score,
                    agent.risk_level, agent.max_severity, agent.posture_grade, agent.final_decision,
                    agent.finding_count, agent.tool_count, agent.first_seen.isoformat(),
                    agent.last_seen.isoformat(), agent.scan_count,
                    agent.model_dump_json(),
                ),
            )
            conn.commit()
            return is_new
        finally:
            conn.close()


def list_agents(
    framework: Optional[str] = None,
    source: Optional[str] = None,
    risk_level: Optional[str] = None,
    owner: Optional[str] = None,
) -> list[Agent]:
    init_db()
    with _lock:
        conn = _connect()
        try:
            clauses: list[str] = []
            params: list[object] = []
            if framework:
                clauses.append("framework = ?")
                params.append(framework)
            if source:
                clauses.append("source = ?")
                params.append(source)
            if risk_level:
                clauses.append("risk_level = ?")
                params.append(risk_level)
            if owner:
                clauses.append("owner = ?")
                params.append(owner)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            rows = conn.execute(
                f"SELECT payload FROM agents{where} ORDER BY risk_score DESC, name ASC",
                params,
            ).fetchall()
            return [Agent.model_validate_json(row["payload"]) for row in rows]
        finally:
            conn.close()


def get_agent(agent_id: str) -> Optional[Agent]:
    init_db()
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT payload FROM agents WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            return Agent.model_validate_json(row["payload"]) if row else None
        finally:
            conn.close()


def clear_all() -> int:
    init_db()
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM agents")
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()


def _parse_dt(value: object, fallback):
    from datetime import datetime

    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return fallback
