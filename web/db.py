"""
Lightweight SQLite store for test run history.
Database lives at  <project_root>/reports/runs.db
"""

import json
import sqlite3
import pathlib
import os
from contextlib import closing
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = pathlib.Path(os.environ.get('ASSESSMENT_DB', str(ROOT / 'reports' / 'runs.db')))


def _connect() -> sqlite3.Connection:
    from flask import current_app, has_app_context
    path = pathlib.Path(current_app.config['DATABASE_PATH']) if has_app_context() else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            suite       TEXT    NOT NULL,          -- 'python' | 'sql' | 'cpp'
            ran_at      TEXT    NOT NULL,           -- ISO-8601 UTC
            passed      INTEGER NOT NULL,
            failed      INTEGER NOT NULL,
            skipped     INTEGER DEFAULT 0,
            exit_code   INTEGER NOT NULL,
            raw_output  TEXT
        );
        CREATE TABLE IF NOT EXISTS case_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      INTEGER NOT NULL REFERENCES runs(id),
            problem_id  TEXT    NOT NULL,
            case_num    INTEGER,
            status      TEXT    NOT NULL,           -- 'pass' | 'fail' | 'error' | 'skip'
            detail      TEXT
        );
    """)
    conn.commit()
    return conn


# ── parsers ──────────────────────────────────────────────────────────────────

import re

def _parse_python_output(output: str) -> tuple[int, int, int, list[dict]]:
    """Return (passed, failed, skipped, case_rows) from run_python_tests output."""
    cases = []
    for line in output.splitlines():
        m = re.match(r"\[(PASS|FAIL|ERROR|SKIP)\]\s+(DSA\w+)\s+case\s+(\d+):?(.*)", line)
        if m:
            status = {"PASS": "pass", "FAIL": "fail", "ERROR": "error", "SKIP": "skip"}[m.group(1)]
            cases.append({"problem_id": m.group(2), "case_num": int(m.group(3)),
                          "status": status, "detail": m.group(4).strip()})
    m = re.search(r"Result:\s*(\d+)\s+passed,\s*(\d+)\s+failed", output)
    passed = int(m.group(1)) if m else 0
    failed = int(m.group(2)) if m else 0
    return passed, failed, 0, cases


def _parse_sql_output(output: str) -> tuple[int, int, int, list[dict]]:
    cases = []
    for line in output.splitlines():
        m = re.match(r"\[(PASS|FAIL|ERROR|SKIP)\]\s+(SQL\w+)(?:\s+case\s+(\d+))?:?(.*)", line)
        if m:
            status = {"PASS": "pass", "FAIL": "fail", "ERROR": "error", "SKIP": "skip"}[m.group(1)]
            cases.append({"problem_id": m.group(2), "case_num": int(m.group(3)) if m.group(3) else None,
                          "status": status, "detail": m.group(4).strip()})
    m = re.search(r"Result:\s*(\d+)\s+passed,\s*(\d+)\s+failed,\s*(\d+)\s+skipped", output)
    passed  = int(m.group(1)) if m else 0
    failed  = int(m.group(2)) if m else 0
    skipped = int(m.group(3)) if m else 0
    return passed, failed, skipped, cases


def _parse_cpp_output(output: str) -> tuple[int, int, int, list[dict]]:
    cases = []
    for line in output.splitlines():
        m = re.match(r"\[(PASS|FAIL|ERROR|SKIP)\]\s+(DSA\w+)\s+case\s+(\d+):?(.*)", line)
        if m:
            status = {"PASS": "pass", "FAIL": "fail", "ERROR": "error", "SKIP": "skip"}[m.group(1)]
            cases.append({"problem_id": m.group(2), "case_num": int(m.group(3)),
                          "status": status, "detail": m.group(4).strip()})
    m = re.search(r"Result:\s*(\d+)\s+passed,\s*(\d+)\s+failed", output)
    passed = int(m.group(1)) if m else 0
    failed = int(m.group(2)) if m else 0
    return passed, failed, 0, cases


_PARSERS = {
    "python": _parse_python_output,
    "sql":    _parse_sql_output,
    "cpp":    _parse_cpp_output,
    "adversarial": _parse_python_output,
}


# ── public API ───────────────────────────────────────────────────────────────

def record_run(suite: str, output: str, exit_code: int) -> int:
    """Parse output, persist run + case rows, return run id."""
    parser = _PARSERS.get(suite)
    if parser is None:
        raise ValueError('Unknown suite')
    passed, failed, skipped, cases = parser(output)
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            'INSERT INTO runs (suite, ran_at, passed, failed, skipped, exit_code, raw_output) '
            'VALUES (?,?,?,?,?,?,?)',
            (suite, datetime.now(timezone.utc).isoformat(), passed, failed, skipped, exit_code, output)
        )
        run_id = cur.lastrowid
        for case in cases:
            conn.execute(
                'INSERT INTO case_results (run_id, problem_id, case_num, status, detail) '
                'VALUES (?,?,?,?,?)',
                (run_id, case['problem_id'], case['case_num'], case['status'], case['detail'])
            )
    return run_id


def get_runs(limit: int = 50) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analytics(bank_problems: list[dict]) -> dict:
    """
    Return aggregated stats for the analytics page.
    All numbers are derived from the question bank + run history.
    """
    conn = _connect()

    # ── bank-level stats (no runs needed) ───────────────────────────────────
    by_difficulty: dict[str, dict] = {}
    by_topic:      dict[str, dict] = {}
    by_category:   dict[str, dict] = {}

    for p in bank_problems:
        for bucket, key in [(by_difficulty, p["difficulty"]),
                            (by_topic,      p["topic"]),
                            (by_category,   p["category"].upper())]:
            bucket.setdefault(key, {"total": 0, "passed": 0, "failed": 0})
            bucket[key]["total"] += 1

    # ── per-problem pass rates from case_results ─────────────────────────────
    rows = conn.execute("""
        SELECT problem_id,
               SUM(CASE WHEN status='pass'  THEN 1 ELSE 0 END) AS p,
               SUM(CASE WHEN status IN ('fail','error') THEN 1 ELSE 0 END) AS f
        FROM case_results
        GROUP BY problem_id
    """).fetchall()

    problem_stats: dict[str, dict] = {}
    for r in rows:
        problem_stats[r["problem_id"]] = {"passed": r["p"], "failed": r["f"]}

    # map problem stats → buckets
    for p in bank_problems:
        pid  = p["id"]
        stat = problem_stats.get(pid, {"passed": 0, "failed": 0})
        for bucket, key in [(by_difficulty, p["difficulty"]),
                            (by_topic,      p["topic"]),
                            (by_category,   p["category"].upper())]:
            bucket[key]["passed"] += stat["passed"]
            bucket[key]["failed"] += stat["failed"]

    # ── run trend (last 20 runs) ─────────────────────────────────────────────
    trend_rows = conn.execute("""
        SELECT ran_at, suite, passed, failed
        FROM runs ORDER BY id DESC LIMIT 20
    """).fetchall()
    trend = [dict(r) for r in reversed(trend_rows)]

    # ── top failing problems ─────────────────────────────────────────────────
    top_fail_rows = conn.execute("""
        SELECT problem_id,
               SUM(CASE WHEN status IN ('fail','error') THEN 1 ELSE 0 END) AS failures
        FROM case_results
        GROUP BY problem_id
        HAVING failures > 0
        ORDER BY failures DESC
        LIMIT 8
    """).fetchall()
    top_failing = [dict(r) for r in top_fail_rows]

    # ── summary counts ───────────────────────────────────────────────────────
    totals = conn.execute(
        "SELECT SUM(passed) AS p, SUM(failed) AS f, COUNT(*) AS runs, "
        "SUM(CASE WHEN exit_code != 0 THEN 1 ELSE 0 END) AS failed_runs FROM runs"
    ).fetchone()

    conn.close()

    return {
        "by_difficulty": by_difficulty,
        "by_topic":      by_topic,
        "by_category":   by_category,
        "trend":         trend,
        "top_failing":   top_failing,
        "total_runs":    totals["runs"] or 0,
        "total_passed":  totals["p"]    or 0,
        "total_failed":  totals["f"]    or 0,
        "failed_runs": totals['failed_runs'] or 0,
        "bank_size":     len(bank_problems),
    }
