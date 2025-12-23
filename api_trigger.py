from fastapi import FastAPI
import subprocess
import sys

app = FastAPI(title="DemoAPI Test Trigger", version="1.0")

@app.post("/run-tests")
def run_tests():
    cmd = [sys.executable, "run_demo.py"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    exit_code = p.returncode
    status = "SUCCESS" if exit_code == 0 else "FAILED"

    out_lines = (p.stdout or "").splitlines()[-120:]
    err_lines = (p.stderr or "").splitlines()[-120:]

    return {
        "status": status,
        "exit_code": exit_code,
        "stdout_tail": out_lines,
        "stderr_tail": err_lines
    }
