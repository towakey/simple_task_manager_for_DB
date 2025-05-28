"""
SQLite database access layer for simple_task_manager.

This module provides CRUD helpers so that legacy "index.py" code can be refactored
incrementally.  All datetime strings are stored in ISO format ("YYYY-MM-DDTHH:MM:SS").
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

_DB_FILENAME = "tasks.db"

_lock = threading.Lock()
_connection: Optional[sqlite3.Connection] = None


###############################################################################
# Internal helpers
###############################################################################

def _get_connection() -> sqlite3.Connection:
    """Return a singleton connection instance (thread-safe)."""
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                script_path = os.path.dirname(__file__)
                db_path = os.path.join(script_path, _DB_FILENAME)
                _connection = sqlite3.connect(db_path, check_same_thread=False)
                _connection.row_factory = sqlite3.Row
    return _connection


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a DB row to a plain dict with appropriate type conversions."""
    if row is None:
        return {}
    result = dict(row)
    # Convert int flags to bool
    result["pinned"] = bool(result.get("pinned", 0))
    # Convert comma separated strings back to list for tags
    tags = result.get("tags", "")
    result["tags"] = [t for t in tags.split(",") if t] if isinstance(tags, str) else []
    return result


###############################################################################
# Public API
###############################################################################

def init_db() -> None:
    """Create the tasks table if it doesn't exist."""
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                create_date TEXT NOT NULL,
                update_date TEXT NOT NULL,
                complete_date TEXT,
                pinned INTEGER NOT NULL DEFAULT 0,
                category TEXT,
                group_category TEXT,
                担当者 TEXT,
                大分類 TEXT,
                中分類 TEXT,
                小分類 TEXT,
                regular TEXT DEFAULT 'Regular',
                report_flag INTEGER NOT NULL DEFAULT 0,
                content TEXT,
                tags TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_pinned ON tasks(pinned)")
        

def insert(task: Dict[str, Any]) -> str:
    """Insert a task. Returns the task id (generated if missing)."""
    conn = _get_connection()

    task_id = task.get("id") or str(uuid.uuid4())
    now = datetime.utcnow().isoformat(timespec="seconds")

    # Prepare defaults
    data = {
        "id": task_id,
        "name": task.get("name", ""),
        "status": task.get("status", "CONTINUE"),
        "create_date": task.get("create_date", now),
        "update_date": task.get("update_date", now),
        "complete_date": task.get("complete_date"),
        "pinned": int(bool(task.get("pinned", False))),
        "category": task.get("category"),
        "group_category": task.get("groupCategory"),
        "担当者": task.get("担当者"),
        "大分類": task.get("大分類"),
        "中分類": task.get("中分類"),
        "小分類": task.get("小分類"),
        "regular": task.get("regular", "Regular"),
        "report_flag": int(bool(task.get("report_flag", False))),
        "content": task.get("content", ""),
        "tags": ",".join(task.get("tags", [])) if isinstance(task.get("tags"), list) else task.get("tags", ""),
    }

    with conn:
        conn.execute(
            """
            INSERT INTO tasks (
                id,name,status,create_date,update_date,complete_date,
                pinned,category,group_category,担当者,大分類,中分類,小分類,regular,report_flag,content,tags
            ) VALUES (
                :id,:name,:status,:create_date,:update_date,:complete_date,
                :pinned,:category,:group_category,:担当者,:大分類,:中分類,:小分類,:regular,:report_flag,:content,:tags
            )
            """,
            data,
        )
    return task_id


def fetch_one(task_id: str) -> Dict[str, Any]:
    """Fetch a single task by id. Returns a dict or empty if not found."""
    conn = _get_connection()
    cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    return _row_to_dict(row) if row else {}


def fetch_all(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Fetch all tasks applying optional simple equality filters."""
    sql = "SELECT * FROM tasks"
    params: List[Any] = []
    if filters:
        clauses = []
        for key, value in filters.items():
            clauses.append(f"{key} = ?")
            params.append(value)
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY pinned DESC, update_date DESC"

    conn = _get_connection()
    cur = conn.execute(sql, params)
    return [_row_to_dict(row) for row in cur.fetchall()]


def update(task_id: str, updates: Dict[str, Any]) -> bool:
    """Update a task. Returns True if a row was updated."""
    if not updates:
        return False
    conn = _get_connection()
    updates["update_date"] = updates.get("update_date", datetime.utcnow().isoformat(timespec="seconds"))

    # Convert boolean and list fields
    if "pinned" in updates:
        updates["pinned"] = int(bool(updates["pinned"]))
    if "tags" in updates and isinstance(updates["tags"], list):
        updates["tags"] = ",".join(updates["tags"])

    set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
    updates["id"] = task_id
    with conn:
        cur = conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = :id", updates)
    return cur.rowcount > 0


def delete(task_id: str) -> bool:
    """Delete a task. Returns True if a row was removed."""
    conn = _get_connection()
    with conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount > 0


# Initialize DB on import (can be skipped if caller wants explicit call)
init_db()
