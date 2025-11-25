"""
A lightweight two-agent composition using ADK style patterns:
- OpsCoordinatorAgent: receives requests, delegates to worker agents (parallel or sequential)
- OpsWorkerAgent: performs tasks using tools (GitHub / code exec)
This is intentionally framework-light so it runs without heavy ADK bootstrapping,
but shows the same conceptual constructs (multi-agent, tools, sessions, long-run).
"""
import logging
import time
import threading
from typing import Dict, Any, List
from tools.github_openapi import GitHubOpenAPI
from tools.code_executor import CodeExecutor
from infra.prometheus_metrics import Metrics

logger = logging.getLogger("ops_agent")

class OpsWorkerAgent:
    def __init__(self, name: str, tools: Dict[str, Any], session, metrics: Metrics):
        self.name = name
        self.tools = tools
        self.session = session
        self.metrics = metrics

    def perform(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the task. Simulate long-running op for certain tasks."""
        self.metrics.inc_counter("worker_tasks_total")
        logger.info("[%s] starting task: %s", self.name, task)
        task_type = task.get("task", "")

        # simple tool-driven task
        if "repo" in task_type or "repo" in task:
            # call GitHub tool
            gh = self.tools.get("github")
            issues = gh.search_issues("repo:your-org/your-repo is:open")  # placeholder query
            result = {"worker": self.name, "type":"github_search", "issues_count": len(issues)}
            logger.info("[%s] github search found %d items", self.name, len(issues))
        elif "execute" in task_type or "run" in task_type:
            exec_tool = self.tools.get("exec")
            out = exec_tool.run(["echo", "hello from exec"])
            result = {"worker": self.name, "type":"exec", "output": out}
        else:
            # simulate long-running
            logger.info("[%s] simulating long-running op (5s)", self.name)
            for i in range(5):
                time.sleep(1)
                self.metrics.inc_counter("worker_heartbeat_total")
            result = {"worker": self.name, "type":"simulated", "status":"done"}

        # save to session (small example)
        self.session.write(f"{self.name}-last", result)
        logger.info("[%s] task finished: %s", self.name, result)
        return result

class OpsCoordinatorAgent:
    def __init__(self, session, metrics: Metrics):
        self.session = session
        self.metrics = metrics
        # tools
        self.tools = {
            "github": GitHubOpenAPI(),
            "exec": CodeExecutor()
        }
        # initialize workers
        self.workers = [OpsWorkerAgent("worker-1", self.tools, session, metrics),
                        OpsWorkerAgent("worker-2", self.tools, session, metrics)]

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrate both sequential and parallel patterns depending on request.
        - If request contains 'parallel' -> run workers in parallel
        - Else run sequentially and compose outputs
        """
        self.metrics.inc_counter("requests_total")
        mode = "parallel" if ("parallel" in request.get("task","").lower()) else "sequential"
        results = []

        if mode == "parallel":
            threads: List[threading.Thread] = []
            res_lock = threading.Lock()
            def run_worker(w):
                r = w.perform(request)
                with res_lock:
                    results.append(r)
            for w in self.workers:
                t = threading.Thread(target=run_worker, args=(w,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
        else:
            # sequential delegation
            for w in self.workers:
                r = w.perform(request)
                results.append(r)

        # simple evaluation metric: success if at least one worker completed
        success = any(r.get("status","done") == "done" or r.get("issues_count",0) >= 0 for r in results)
        self.metrics.set_gauge("last_request_success", 1 if success else 0)
        # persist composed result
        out = {"request_id": request.get("id"), "mode": mode, "results": results}
        self.session.write(f"req-{request.get('id')}", out)
        return out
