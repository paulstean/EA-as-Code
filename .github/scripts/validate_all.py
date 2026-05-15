#!/usr/bin/env python3
"""Run all validation suites: catalogs and skills."""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(name):
    print(f"\n{'=' * 70}", flush=True)
    print(f"  Running {name}", flush=True)
    print(f"{'=' * 70}", flush=True)
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, name)],
        capture_output=False,
        env=env
    )
    return result.returncode


if __name__ == "__main__":
    exit_code = 0
    exit_code |= run_script("validate_catalogs.py")
    exit_code |= run_script("validate_skills.py")
    sys.exit(exit_code)
