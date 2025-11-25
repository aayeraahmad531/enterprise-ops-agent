# agents/adk_runner.py
"""
Small programmatic runner for the ADK ops agent.
Run: python -m agents.adk_runner
This will read input lines and call the ADK agent's run_one_shot method.
"""
from agents.adk_ops_agent import handle_text_request
import sys, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adk_runner")

def main():
    print("ADK Ops Runner — type a request and press enter (ctrl-c to quit).")
    try:
        while True:
            text = input("Request> ").strip()
            if not text:
                continue
            out = handle_text_request(text)
            print("Agent output:", out)
    except KeyboardInterrupt:
        print("\nBye.")

if __name__ == "__main__":
    main()
