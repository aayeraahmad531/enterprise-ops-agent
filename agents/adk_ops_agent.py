# agents/adk_ops_agent.py
"""
Simplified, robust ADK ops agent wrapper.

Behavior:
- Try importing ADK classes, but if *any* incompatibility arises when creating ADK tools/agent,
  we immediately disable ADK usage and continue with a reliable local SimpleAgent fallback.
- This avoids pydantic validation errors and keeps the CLI runner stable in Codespaces.
- All fallback behavior is logged so you can later enable ADK when you have a matching ADK version.

This file intentionally keeps the fallback simple: it supports a summarize tool and simple repo/issue
responses. It is safe to run without ADK, and will provide consistent outputs.
"""
import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger("adk_ops_agent")
logger.setLevel(logging.INFO)

# -------------------------
# 1) Summarize tool (local)
# -------------------------
def summarize_incident(text: str) -> Dict[str, str]:
    """Return a short incident summary. Input: raw incident text."""
    if not text:
        return {"status": "error", "summary": ""}
    summary = text.strip().replace("\n", " ")
    if len(summary) > 280:
        summary = summary[:277] + "..."
    return {"status": "ok", "summary": summary}

# -------------------------
# 2) Try ADK imports but disable ADK if incompatible
# -------------------------
ADK_PRESENT = False
ADK_USABLE = False
_adk_import_error = None

try:
    # attempt to import common ADK primitives (may exist or not)
    from google.adk.agents.llm_agent import Agent as ADKAgent  # type: ignore
    from google.adk.tools import FunctionTool as ADKFunctionTool  # type: ignore
    from google.adk.tools import OpenAPIToolset as ADKOpenAPIToolset  # type: ignore
    from google.adk.session import InMemorySessionService as ADKInMemorySession  # type: ignore
    ADK_PRESENT = True
    logger.info("ADK package found. Will attempt to use it if compatible.")
except Exception as e:
    _adk_import_error = e
    ADK_PRESENT = False
    logger.info("ADK not available or imports failed — using fallback SimpleAgent. Error: %s", e)

# -------------------------
# 3) Local fallback classes
# -------------------------
class SimpleFunctionTool:
    """Wrap a Python callable as a lightweight tool."""
    def __init__(self, fn, name: str):
        self.fn = fn
        self.name = name

    def call(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

class SimpleAgent:
    """
    Minimal "agent" interface with run_one_shot(text).
    - recognizes 'summarize' and calls summarize_incident
    - recognizes 'repo', 'issue', 'search' and returns a note that OpenAPI isn't available (or simulates)
    - otherwise echoes the input
    """
    def __init__(self, tools: List[Any] = None, name: str = "simple_agent"):
        self.tools = {}
        if tools:
            for t in tools:
                key = getattr(t, "name", f"tool_{len(self.tools)}")
                self.tools[key] = t
        self.name = name

    def run_one_shot(self, text: str) -> Dict[str, Any]:
        text_l = text.lower() if text else ""
        if "summarize" in text_l or "summary" in text_l:
            # pick a summarize tool if present
            summ = None
            for k, v in self.tools.items():
                if "summarize" in k or "summ" in k:
                    summ = v
                    break
            if summ:
                try:
                    if hasattr(summ, "call"):
                        return {"tool_used": getattr(summ, "name", "summ_tool"), "result": summ.call(text)}
                    elif callable(summ):
                        return {"tool_used": getattr(summ, "name", "summ_tool"), "result": summ(text)}
                except Exception as e:
                    return {"error": str(e)}
            return {"tool_used": None, "result": summarize_incident(text)}
        if "repo" in text_l or "issue" in text_l or "search" in text_l:
            # if GitHub spec exists, we can hint that the user can download & use it; otherwise give a simulated response
            spec_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "tools", "api.github.com.json"))
            if os.path.exists(spec_path):
                return {"note": "OpenAPI spec present but ADK OpenAPIToolset is not enabled in this environment.", "spec": spec_path}
            else:
                return {"note": "No GitHub OpenAPI spec found. To enable real repo queries, run tools/api.github.download_spec.py"}
        # default
        return {"note": "echo", "input": text[:200]}

# -------------------------
# 4) Build tool list and decide ADK usability
# -------------------------
# Always make a local summarize tool wrapper
local_summ_tool = SimpleFunctionTool(summarize_incident, name="summarize_incident")

tools_list = [local_summ_tool]

# Add OpenAPI info if spec exists (we will not attempt to auto-generate ADK tools here)
spec_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "tools", "api.github.com.json"))
if os.path.exists(spec_path):
    logger.info("Found GitHub OpenAPI spec at %s (will note this in responses).", spec_path)
else:
    logger.info("GitHub OpenAPI spec not present at %s.", spec_path)

# If ADK is present, attempt to construct ADK-compat tools/agent but bail out on any validation error
if ADK_PRESENT:
    try:
        # Attempt to create an ADK FunctionTool if its constructor matches our usage.
        # Because ADK versions vary, this may raise; if it does, we will mark ADK unusable.
        try:
            adk_summ_tool = ADKFunctionTool(fn=summarize_incident, name="summarize_incident")
            # if we succeeded, include it
            tools_list = [adk_summ_tool]
            logger.info("Constructed ADK FunctionTool successfully.")
        except TypeError:
            # constructor signature doesn't match; ADK in this environment is incompatible for our quick demo
            logger.warning("ADK FunctionTool signature mismatch; will not use ADK agent in this environment.")
            raise RuntimeError("ADK FunctionTool signature mismatch")
        # Try build a session service
        try:
            adk_session = ADKInMemorySession()
            # Try to instantiate the ADK agent with a minimal/shallow constructor to test compatibility
            try:
                test_agent = ADKAgent(name="ops_root_agent_test", tools=tools_list)
            except Exception as e:
                logger.warning("ADK Agent instantiation failed during compatibility test: %s", e)
                raise RuntimeError("ADK Agent instantiation failed")
            # If we get here, ADK seems usable
            ADK_USABLE = True
            root_agent = test_agent  # keep this as the agent (but we will wrap run_one_shot usage)
            logger.info("ADK appears usable in this environment.")
        except Exception as e:
            logger.warning("ADK session/agent compatibility failed: %s", e)
            ADK_USABLE = False
    except Exception as compat_err:
        ADK_USABLE = False
        logger.info("ADK disabled due to compatibility: %s", compat_err)
else:
    ADK_USABLE = False

# If ADK unusable, fall back to SimpleAgent
if not ADK_USABLE:
    logger.info("Falling back to SimpleAgent (ADK not usable or incompatible).")
    root_agent = SimpleAgent(tools=tools_list, name="fallback_ops_root_agent")

# Expose the single helper the runner uses
def handle_text_request(text: str):
    """
    Run the configured agent (ADK agent if usable -> run_one_shot, else SimpleAgent)
    and return a Python-serializable dict.
    """
    logger.info("handle_text_request called. ADK_USABLE=%s Text=%s", ADK_USABLE, (text[:200] if text else text))
    if ADK_USABLE:
        # try multiple possible run methods to be robust
        try:
            if hasattr(root_agent, "run_one_shot"):
                out = root_agent.run_one_shot(text)
                return {"agent": getattr(root_agent, "name", "adk_agent"), "result": out}
            if hasattr(root_agent, "run"):
                out = root_agent.run(text)
                return {"agent": getattr(root_agent, "name", "adk_agent"), "result": out}
        except Exception as e:
            logger.exception("ADK agent run failed; falling back to SimpleAgent: %s", e)
            # fall through to fallback handling

    # fallback path
    try:
        out = root_agent.run_one_shot(text)
        return {"agent": getattr(root_agent, "name", "fallback_agent"), "result": out}
    except Exception as e:
        logger.exception("Fallback agent run failed: %s", e)
        return {"error": str(e)}
