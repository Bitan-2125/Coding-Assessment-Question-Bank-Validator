"""
Flask web interface for the Coding Assessment Question Bank.
Run from project root:  python web/app.py
Then open http://127.0.0.1:5000
"""

import csv
import io
import json
import pathlib
import subprocess
import sys

from flask import Flask, jsonify, render_template, request, Response

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "question_bank.json"
TESTS_DIR = ROOT / "tests"

app = Flask(__name__, template_folder="templates", static_folder="static")

# import after app is created so ROOT is set
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import db as rundb


# ── helpers ──────────────────────────────────────────────────────────────────

def load_bank():
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def _run_suite(script: str, suite: str, timeout: int = 60):
    result = subprocess.run(
        [sys.executable, str(TESTS_DIR / script)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=timeout,
    )
    output = result.stdout + result.stderr
    run_id = rundb.record_run(suite, output, result.returncode)
    return jsonify({"output": output, "exit_code": result.returncode, "run_id": run_id})


# ── pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    bank = load_bank()
    problems = bank["problems"]
    topic    = request.args.get("topic", "")
    diff     = request.args.get("difficulty", "")
    category = request.args.get("category", "")
    topics       = sorted({p["topic"]    for p in problems})
    difficulties = ["Easy", "Medium", "Hard"]
    categories   = sorted({p["category"] for p in problems})
    if topic:
        problems = [p for p in problems if p["topic"] == topic]
    if diff:
        problems = [p for p in problems if p["difficulty"] == diff]
    if category:
        problems = [p for p in problems if p["category"] == category]
    return render_template(
        "index.html", problems=problems,
        topics=topics, difficulties=difficulties, categories=categories,
        selected_topic=topic, selected_diff=diff, selected_category=category,
        total=len(problems),
    )


@app.route("/question/<problem_id>")
def question(problem_id):
    bank = load_bank()
    problem = next((p for p in bank["problems"] if p["id"] == problem_id), None)
    if problem is None:
        return "Not found", 404
    return render_template("question.html", p=problem)


@app.route("/run-tests")
def run_tests_page():
    return render_template("run_tests.html")


@app.route("/analytics")
def analytics():
    bank = load_bank()
    stats = rundb.get_analytics(bank["problems"])
    runs  = rundb.get_runs(limit=20)
    return render_template("analytics.html", stats=stats, runs=runs)


# ── test runner APIs ──────────────────────────────────────────────────────────

@app.route("/api/run-python-tests", methods=["POST"])
def api_run_python():
    return _run_suite("run_python_tests.py", "python", timeout=30)


@app.route("/api/run-sql-tests", methods=["POST"])
def api_run_sql():
    return _run_suite("run_sql_tests.py", "sql", timeout=30)


@app.route("/api/run-cpp-tests", methods=["POST"])
def api_run_cpp():
    return _run_suite("run_cpp_tests.py", "cpp", timeout=60)


# ── CSV export ────────────────────────────────────────────────────────────────

@app.route("/export/runs.csv")
def export_runs_csv():
    runs = rundb.get_runs(limit=1000)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "suite", "ran_at", "passed", "failed",
                                             "skipped", "exit_code"])
    writer.writeheader()
    for r in runs:
        writer.writerow({k: r[k] for k in writer.fieldnames})
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_runs.csv"},
    )


@app.route("/export/case-results.csv")
def export_cases_csv():
    conn = rundb._connect()
    rows = conn.execute("""
        SELECT cr.id, r.suite, r.ran_at, cr.problem_id, cr.case_num, cr.status, cr.detail
        FROM case_results cr
        JOIN runs r ON r.id = cr.run_id
        ORDER BY cr.id DESC
        LIMIT 5000
    """).fetchall()
    conn.close()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "suite", "ran_at", "problem_id",
                                             "case_num", "status", "detail"])
    writer.writeheader()
    for r in rows:
        writer.writerow(dict(r))
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=case_results.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
