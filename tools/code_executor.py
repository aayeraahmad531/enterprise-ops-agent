"""
Simple code execution tool. WARNING: running arbitrary commands is dangerous.
This demo uses it only for safe echo commands. In production, wrap/validate commands, run in sandbox.
"""
import subprocess
import logging

logger = logging.getLogger("code_executor")

class CodeExecutor:
    def run(self, cmd):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {"returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
        except Exception as e:
            logger.exception("Exec failed")
            return {"error": str(e)}
