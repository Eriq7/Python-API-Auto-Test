from fastapi import FastAPI
import subprocess
import sys

app = FastAPI(title="DemoAPI Test Trigger", version="1.0")

@app.post("/run-tests")
def run_tests():
    """
    Synchronous trigger:
    - runs: python run_demo.py
    - returns: status + exit_code + report path lines (stdout tail)
    """
    cmd = [sys.executable, "run_demo.py"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    exit_code = p.returncode
    status = "SUCCESS" if exit_code == 0 else "FAILED"

    # Return last ~80 lines for debugging in Jenkins console
    out_lines = (p.stdout or "").splitlines()[-80:]
    err_lines = (p.stderr or "").splitlines()[-80:]

    return {
        "status": status,
        "exit_code": exit_code,
        "stdout_tail": out_lines,
        "stderr_tail": err_lines
    }
