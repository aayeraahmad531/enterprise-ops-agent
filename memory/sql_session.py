"""
SQLite-backed session store.
Simple key/value store that persists JSON-serializable values.
Works well in Codespaces and persists between runs.
"""
import sqlite3
import json
import threading
from typing import Any, Optional

DB_PATH = "session_store.sqlite3"

class SQLiteSession:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS session (key TEXT PRIMARY KEY, value TEXT, updated_at INTEGER)"
            )
            conn.commit()

    def write(self, key: str, value: Any):
        payload = json.dumps(value, default=str)
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO session(key, value, updated_at) VALUES (?, ?, strftime('%s','now')) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=strftime('%s','now')",
                (key, payload),
            )
            conn.commit()

    def read(self, key: str, default: Optional[Any] = None):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM session WHERE key=?", (key,))
            row = cur.fetchone()
            if not row:
                return default
            try:
                return json.loads(row[0])
            except Exception:
                return row[0]

    def all(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM session")
            rows = cur.fetchall()
            out = {}
            for k, v in rows:
                try:
                    out[k] = json.loads(v)
                except Exception:
                    out[k] = v
            return out
agents/long_running_manager.py
python
Copy code
# agents/long_running_manager.py
"""
MCP-style Long Running Operation Manager (pause/resume/inspect).
- Each operation runs in its own thread.
- Status saved to SQLite Session (memory/sql_session.py).
- Exposes a simple CLI to start/pause/resume/list operations.
"""
import threading
import time
import uuid
import logging
from typing import Dict, Any
from memory.sql_session import SQLiteSession
from infra.prometheus_metrics import Metrics

logger = logging.getLogger("long_runner")
logger.setLevel(logging.INFO)

# Initialize session and metrics (import-safe)
session = SQLiteSession()
metrics = Metrics()

# in-memory task registry for thread handles (not persisted)
TASKS: Dict[str, Dict] = {}
TASK_LOCK = threading.Lock()

def _simulate_task(op_id: str, duration: int = 10):
    """A simulated long-running operation that supports pause/resume."""
    logger.info("Task %s starting simulated run %ds", op_id, duration)
    steps = max(1, duration)
    for i in range(steps):
        # check status from session
        st = session.read(f"op:{op_id}:meta", {})
        if st.get("status") == "paused":
            logger.info("Task %s paused at step %d", op_id, i)
            # block until resumed
            while True:
                time.sleep(0.5)
                st = session.read(f"op:{op_id}:meta", {})
                if st.get("status") == "running":
                    logger.info("Task %s resumed", op_id)
                    break
                if st.get("status") == "cancelled":
                    logger.info("Task %s cancelled during pause", op_id)
                    session.write(f"op:{op_id}:result", {"status":"cancelled"})
                    metrics.inc_counter("ops_cancelled_total")
                    return
        # simulate work
        time.sleep(1)
        session.write(f"op:{op_id}:progress", {"step": i + 1, "total": steps})
        metrics.inc_counter("ops_heartbeat_total")
    # done
    result = {"status": "finished", "completed_at": int(time.time())}
    session.write(f"op:{op_id}:result", result)
    meta = session.read(f"op:{op_id}:meta", {})
    meta["status"] = "finished"
    session.write(f"op:{op_id}:meta", meta)
    metrics.inc_counter("ops_finished_total")
    logger.info("Task %s finished", op_id)

def start_operation(duration: int = 10, metadata: Dict[str, Any] = None) -> str:
    op_id = str(uuid.uuid4())
    meta = {"status": "running", "duration": duration, "created_at": int(time.time())}
    if metadata:
        meta.update(metadata)
    session.write(f"op:{op_id}:meta", meta)
    session.write(f"op:{op_id}:progress", {"step": 0, "total": duration})
    TASKS[op_id] = {"thread": None}
    t = threading.Thread(target=_simulate_task, args=(op_id, duration), daemon=True)
    TASKS[op_id]["thread"] = t
    t.start()
    metrics.inc_counter("ops_started_total")
    logger.info("Started operation %s duration=%s", op_id, duration)
    return op_id

def pause_operation(op_id: str) -> bool:
    meta = session.read(f"op:{op_id}:meta", None)
    if not meta:
        return False
    meta["status"] = "paused"
    session.write(f"op:{op_id}:meta", meta)
    metrics.inc_counter("ops_paused_total")
    logger.info("Paused operation %s", op_id)
    return True

def resume_operation(op_id: str) -> bool:
    meta = session.read(f"op:{op_id}:meta", None)
    if not meta:
        return False
    meta["status"] = "running"
    session.write(f"op:{op_id}:meta", meta)
    metrics.inc_counter("ops_resumed_total")
    logger.info("Resumed operation %s", op_id)
    return True

def cancel_operation(op_id: str) -> bool:
    meta = session.read(f"op:{op_id}:meta", None)
    if not meta:
        return False
    meta["status"] = "cancelled"
    session.write(f"op:{op_id}:meta", meta)
    metrics.inc_counter("ops_cancel_requested_total")
    logger.info("Cancel requested for operation %s", op_id)
    return True

def list_operations() -> Dict[str, Any]:
    # scan session keys (simple approach)
    all_keys = session.all()
    ops = {}
    for k, v in all_keys.items():
        if k.startswith("op:") and k.count(":") >= 2 and k.endswith(":meta"):
            op_id = k.split(":")[1]
            ops[op_id] = ops.get(op_id, {})
            ops[op_id]["meta"] = v
            ops[op_id]["progress"] = session.read(f"op:{op_id}:progress")
            ops[op_id]["result"] = session.read(f"op:{op_id}:result")
    return ops

# Small CLI for manual testing
if __name__ == "__main__":
    print("Long-Running Operation Manager CLI")
    print("Commands: start <seconds>, pause <id>, resume <id>, cancel <id>, list, exit")
    while True:
        try:
            cmd = input("m> ").strip()
            if not cmd:
                continue
            parts = cmd.split()
            if parts[0] == "start":
                dur = int(parts[1]) if len(parts) > 1 else 10
                op = start_operation(duration=dur)
                print("started:", op)
            elif parts[0] == "pause" and len(parts) > 1:
                ok = pause_operation(parts[1]); print("paused:", ok)
            elif parts[0] == "resume" and len(parts) > 1:
                ok = resume_operation(parts[1]); print("resumed:", ok)
            elif parts[0] == "cancel" and len(parts) > 1:
                ok = cancel_operation(parts[1]); print("cancel requested:", ok)
            elif parts[0] == "list":
                import json; print(json.dumps(list_operations(), indent=2))
            elif parts[0] == "exit":
                break
            else:
                print("unknown")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("err", e)