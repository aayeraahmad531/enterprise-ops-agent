"""
Small observability helpers: a Prometheus metrics enricher and a simple logger formatter.
We already have infra.prometheus_metrics.Metrics; this file adds a helper to register
operation-specific metrics when an op starts.
"""
import logging
from infra.prometheus_metrics import Metrics

log = logging.getLogger("observability")
log.setLevel(logging.INFO)

def register_operation_metrics(metrics: Metrics, op_id: str):
    """
    Registers (or initializes) operation-specific gauges/counters if needed.
    For simplicity this function increments a counter to mark operation registration.
    """
    metrics.inc_counter("ops_registered_total")
    log.info("Registered metrics for op %s", op_id)
tests/test_long_running.py
python
Copy code
# tests/test_long_running.py
import time
from agents.long_running_manager import start_operation, pause_operation, resume_operation, list_operations
from memory.sql_session import SQLiteSession

def test_start_and_pause_resume(tmp_path):
    # quick smoke test of start/pause/resume mechanics
    ss = SQLiteSession(db_path=str(tmp_path / "testdb.sqlite3"))
    # swap global session inside module? simpler: call start and ensure ops list updates
    op_id = start_operation(duration=3, metadata={"test":"yes"})
    assert isinstance(op_id, str)
    time.sleep(1)
    ops = list_operations()
    assert op_id in ops
    # pause
    paused = pause_operation(op_id)
    assert paused
    time.sleep(1)
    resumed = resume_operation(op_id)
    assert resumed