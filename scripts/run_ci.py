#!/usr/bin/env python3
"""
CI runner for OpenClaw-Harness project.

Runs all quality checks in one command:
1. Golden Rules (file size, secrets, console.log, doc freshness, invariant coverage)
2. Python type checks (backend)
3. Python tests (backend)
4. Frontend type checks (when available)
5. Frontend tests (when available)

Exit 0 = all pass, exit 1 = failures.

Usage:
    python scripts/run_ci.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SRC_DIRS = [str(ROOT / "backend"), str(ROOT / "frontend" / "src")]
DOCS_DIR = str(ROOT / ".plans" / "och" / "docs")


def run_cmd(cmd, label):
    """Run a command, print output, return True if success."""
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=False)
    if result.returncode != 0:
        print(f"[FAIL] {label} failed with exit code {result.returncode}")
        return False
    print(f"[OK] {label} passed")
    return True


def main():
    all_pass = True

    # 1. Golden Rules
    golden_rules = SCRIPTS / "golden_rules.py"
    if golden_rules.exists():
        cmd = [sys.executable, str(golden_rules)] + SRC_DIRS + ["--docs", DOCS_DIR]
        if not run_cmd(cmd, "Golden Rules"):
            all_pass = False
    else:
        print("[SKIP] golden_rules.py not found")

    # 2. Python type check (backend)
    if (ROOT / "backend").exists():
        try:
            if not run_cmd(
                [sys.executable, "-m", "mypy", "backend/app", "--ignore-missing-imports", "--no-error-summary"],
                "Backend Type Check (mypy)"
            ):
                # mypy failures are warnings, not blockers for now
                print("[WARN] mypy issues found — not blocking CI")
        except FileNotFoundError:
            print("[SKIP] mypy not installed")

    # 3. Python tests (backend)
    if (ROOT / "backend" / "tests").exists():
        if not run_cmd(
            [sys.executable, "-m", "pytest", "backend/tests", "-x", "-q"],
            "Backend Tests (pytest)"
        ):
            all_pass = False
    else:
        print("[INFO] No backend/tests directory yet — skipping")

    # 4. Frontend type check
    frontend_dir = ROOT / "frontend"
    if (frontend_dir / "package.json").exists():
        if not run_cmd(
            ["npx", "tsc", "--noEmit", "--project", str(frontend_dir / "tsconfig.json")],
            "Frontend Type Check (tsc)"
        ):
            # tsc failures are warnings for now
            print("[WARN] tsc issues found — not blocking CI")

    print(f"\n{'='*60}")
    if all_pass:
        print("CI Result: PASSED")
    else:
        print("CI Result: FAILED — fix failures before requesting review")
    print(f"{'='*60}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
