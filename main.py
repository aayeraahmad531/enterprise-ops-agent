"""
Updated main.py — integrates:
- Flask server for /health and /metrics
- Uses SQLite-backed session store if available, otherwise falls back to in-memory session
- Starts the OpsCoordinator demo loop
- Demonstrates long-running operations

Run: python main.py
"""
import threading
import time
import logging
import os
import signal
from flask import Flask, jsonify

# try to import SQLite session if available
try:
    from memory.sql_session import SQLiteSession as SessionStore
    session_store = SessionStore()
    SESSION_TYPE = "sqlite"
except Exception:
    try:
        from memory.session_memory import InMemorySession as SessionStore
        session_store = SessionStore()
        SESSION_TYPE = "inmemory"
    except Exception:
        class _FallbackSess:
            def __init__(self): self._s = {}
            def write(self, k, v): self._s[k] = v
            def read(self, k, default=None): return self._s.get(k, default)
            def all(self): return dict(self._s)
        session_store = _FallbackSess()
        SESSION_TYPE = "dict-fallback"

from agents.ops_agent import OpsCoordinatorAgent
from infra.prometheus_metrics import Metrics

try:
    from agents.long_running_manager import start_operation, pause_operation, resume_operation, list_operations
    LR_AVAILABLE = True
except Exception:
    LR_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("enterprise-ops-agent")

app = Flask(__name__)
metrics = Metrics()
coordinator = OpsCoordinatorAgent(session=session_store, metrics=metrics)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "session_type": SESSION_TYPE})

@app.route("/metrics")
def metrics_endpoint():
    return metrics.metrics_response()

_shutdown = threading.Event()

def run_flask():
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)

def demo_agent_loop():
    logger.info("Starting demo agent loop.")
    demo_requests = [
        {"id": "req-1", "task": "investigate incident: database high latency"},
        {"id": "req-2", "task": "create incident summary for ticket #123"},
        {"id": "req-3", "task": "check repo issues for service backend (parallel)"},
    ]

    for r in demo_requests:
        if _shutdown.is_set(): break
        logger.info("Submitting request: %s", r)
        try:
            resp = coordinator.handle_request(r)
            logger.info("Response: %s", resp)
        except Exception as e:
            logger.exception("Error: %s", e)
        time.sleep(1)

    if LR_AVAILABLE:
        logger.info("Starting long-run operation demo.")
        op_id = start_operation(duration=8, metadata={"demo": True})
        logger.info("Started op %s", op_id)
        time.sleep(2)
        pause_operation(op_id)
        logger.info("Paused op %s", op_id)
        time.sleep(2)
        resume_operation(op_id)
        logger.info("Resumed op %s", op_id)
        for _ in range(12):
            ops = list_operations()
            if ops.get(op_id, {}).get("meta", {}).get("status") == "finished":
                logger.info("Operation finished: %s", ops[op_id].get("result"))
                break
            time.sleep(1)
    else:
        logger.info("Long-running manager not available.")

    logger.info("Demo complete.")


def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received: %s", signum)
    _shutdown.set()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server running on :8000")

    try:
        demo_agent_loop()
        while not _shutdown.is_set(): time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    finally:
        logger.info("Exiting...")