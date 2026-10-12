"""
C++ submission validator.
Compiles candidate C++ file together with harness.cpp, then runs each DSA
test case (for problems that have a C++ harness dispatcher) and checks output.

Usage (from project root):
    python tests/run_cpp_tests.py [candidate.cpp]

If no candidate file is given, it uses cpp/reference_solutions.cpp as the
default (self-test mode).

Requirements: g++ on PATH (C++17).
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "cpp" / "harness.cpp"
BANK = ROOT / "question_bank.json"
DEFAULT_CANDIDATE = ROOT / "cpp" / "reference_solutions.cpp"

# Problems that the harness currently supports
SUPPORTED = {
    "DSA001", "DSA002", "DSA005", "DSA007",
    "DSA008", "DSA009", "DSA010", "DSA012",
    "DSA014", "DSA020",
}

# ── tiny JSON serialiser for test-case args ──────────────────────────────────

def to_json_arg(v):
    """Recursively serialise a Python value to a compact JSON string."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ",".join(to_json_arg(x) for x in v) + "]"
    raise TypeError(f"Cannot serialise {type(v)}")


def args_to_json_line(problem_id: str, args: list) -> str:
    args_str = "[" + ",".join(to_json_arg(a) for a in args) + "]"
    return json.dumps({"problem": problem_id, "args": json.loads(args_str)},
                      separators=(',', ':'))


# ── result normaliser (mirrors Python test runner logic) ────────────────────

def normalise(v):
    """Normalise a value for comparison (sort lists where order doesn't matter)."""
    return v


def results_equal(actual, expected, case: dict) -> bool:
    if "expected_groups" in case:
        norm = lambda groups: sorted(
            (tuple(sorted(g)) for g in groups), key=repr
        )
        return norm(actual) == norm(case["expected_groups"])
    return actual == expected


# ── compile ──────────────────────────────────────────────────────────────────

def compile_candidate(candidate_path: pathlib.Path, out_exe: pathlib.Path) -> tuple[bool, str]:
    cmd = [
        "g++", "-std=c++17", "-O2", "-Wall",
        str(HARNESS), str(candidate_path),
        "-o", str(out_exe),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr
    return True, ""


# ── run one batch of test cases ──────────────────────────────────────────────

def run_tests(exe: pathlib.Path, problems: list) -> tuple[int, int]:
    passed = failed = 0

    for problem in problems:
        pid = problem["id"]
        if pid not in SUPPORTED:
            continue

        for i, case in enumerate(problem.get("test_cases", []), 1):
            args = case["args"]
            line = args_to_json_line(pid, args)

            proc = subprocess.run(
                [str(exe)],
                input=line + "\n",
                capture_output=True,
                text=True,
                timeout=10,
            )

            raw = proc.stdout.strip()
            if proc.returncode != 0 or not raw:
                failed += 1
                print(f"[ERROR] {pid} case {i}: process error — {proc.stderr.strip()}")
                continue

            try:
                actual = json.loads(raw)
            except json.JSONDecodeError:
                failed += 1
                print(f"[ERROR] {pid} case {i}: bad output — {raw!r}")
                continue

            expected = case.get("expected")
            if results_equal(actual, expected, case):
                passed += 1
                print(f"[PASS]  {pid} case {i}")
            else:
                failed += 1
                exp_display = case.get("expected", case.get("expected_groups"))
                print(f"[FAIL]  {pid} case {i}: expected={exp_display!r}, actual={actual!r}")

    return passed, failed


# ── entry point ──────────────────────────────────────────────────────────────

def main():
    candidate = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CANDIDATE
    if not candidate.exists():
        print(f"Candidate file not found: {candidate}")
        sys.exit(1)

    bank = json.loads(BANK.read_text(encoding="utf-8"))
    dsa_problems = [p for p in bank["problems"] if p["category"] == "dsa"]

    print(f"Compiling {candidate.name} + harness.cpp ...")
    with tempfile.TemporaryDirectory() as tmp:
        exe = pathlib.Path(tmp) / "harness_exe"
        ok, err = compile_candidate(candidate, exe)
        if not ok:
            print(f"[COMPILE ERROR]\n{err}")
            sys.exit(1)
        print("Compile OK. Running tests...\n")
        passed, failed = run_tests(exe, dsa_problems)

    print(f"\nResult: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
