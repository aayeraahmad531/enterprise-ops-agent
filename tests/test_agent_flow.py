import time
from agents.ops_agent import OpsCoordinatorAgent
from memory.session_memory import InMemorySession
from infra.prometheus_metrics import Metrics

def test_flow():
    session = InMemorySession()
    metrics = Metrics()
    coord = OpsCoordinatorAgent(session=session, metrics=metrics)
    req = {"id":"test-1", "task":"quick demo run"}
    out = coord.handle_request(req)
    assert out["request_id"] == "test-1"
    assert "results" in out
