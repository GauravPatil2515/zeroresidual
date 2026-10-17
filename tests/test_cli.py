import os
import subprocess
import sys

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CLI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "zeroresidual", "cli.py"))

def test_cli_demo_tieout_exit_0():
    cmd = [sys.executable, CLI_PATH, "demo-tieout", "--no-llm"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0
    assert "RECONCILIATION COMPLETE: 100% TIED OUT" in p.stderr

def test_cli_demo_unexplained_exit_1():
    cmd = [sys.executable, CLI_PATH, "demo-unexplained", "--no-llm"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 1
    assert "UNEXPLAINED RESIDUAL DETECTED" in p.stderr
