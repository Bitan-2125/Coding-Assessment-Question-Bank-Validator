"""
Flask web interface for the Coding Assessment Question Bank.
Run from project root:  python web/app.py
Then open http://127.0.0.1:5000
"""

import csv
import io
import pathlib
import sys
import os
import hmac
import logging
import sqlite3
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request, Response, g, abort
from werkzeug.exceptions import HTTPException

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "question_bank.json"
TESTS_DIR = ROOT / "tests"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.update(
    RUNNER_TOKEN=os.environ.get('ASSESSMENT_RUNNER_TOKEN', ''),
    DATABASE_PATH=os.environ.get('ASSESSMENT_DB', str(ROOT / 'reports' / 'runs.db')),
    MAX_CONTENT_LENGTH=16 * 1024,
    TRUSTED_HOSTS=os.environ.get('ASSESSMENT_TRUSTED_HOSTS', 'localhost,127.0.0.1').split(','),
)
logging.basicConfig(level=os.environ.get('ASSESSMENT_LOG_LEVEL', 'INFO'),
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
RUN_LOCK = threading.Lock()

# import after app is created so ROOT is set
sys.path.insert(0, str(ROOT))
from web import db as rundb
from validation import load_bank as validated_load_bank, BankValidationError
from runner import execute


# ── helpers ──────────────────────────────────────────────────────────────────

def load_bank():
    return validated_load_bank(BANK_PATH)


def _run_suite(suite):
    token = app.config['RUNNER_TOKEN']
    if not token:
        abort(503, description='Test execution is disabled. Configure ASSESSMENT_RUNNER_TOKEN.')
    supplied = request.headers.get('X-Runner-Token', '')
    if not hmac.compare_digest(supplied.encode('utf-8'), token.encode('utf-8')):
        abort(401, description='A valid runner token is required.')
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
        abort(403, description='Cross-origin execution is not allowed.')
    if request.content_length:
        abort(400, description='This endpoint accepts no submission or request body.')
    if not RUN_LOCK.acquire(blocking=False):
        return jsonify(error='A test suite is already running. Try again shortly.',
                       output='Runner busy.', exit_code=1), 409
    try:
        result = execute(suite)
        result['run_id'] = rundb.record_run(suite, result['output'], result['exit_code'])
        status = 504 if result['status'] == 'timeout' else 503 if result['status'] == 'error' else 200
        return jsonify(result), status
    finally:
        RUN_LOCK.release()


@app.before_request
def start_request():
    g.request_id = uuid.uuid4().hex
    g.started_at = time.monotonic()


@app.after_request
def finish_request(response):
    response.headers['X-Request-ID'] = g.get('request_id', '')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    app.logger.info('request_id=%s method=%s path=%s status=%s duration=%.3f',
                    g.get('request_id'), request.method, request.path, response.status_code,
                    time.monotonic() - g.get('started_at', time.monotonic()))
    return response


def error_response(message, status):
    if request.path.startswith('/api/') or request.path == '/healthz':
        return jsonify(error=message, output=message, exit_code=1,
                       request_id=g.get('request_id')), status
    return render_template('error.html', message=message, status=status,
                           request_id=g.get('request_id')), status


@app.errorhandler(HTTPException)
def http_error(exc):
    response = app.make_response(error_response(exc.description, exc.code))
    for key, value in exc.get_headers():
        if key.lower() not in ('content-type', 'content-length'):
            response.headers[key] = value
    return response


@app.errorhandler(BankValidationError)
@app.errorhandler(sqlite3.Error)
def service_error(exc):
    app.logger.exception('Service unavailable request_id=%s', g.get('request_id'))
    return error_response('Validation data or history storage is unavailable. Check server logs.', 503)


@app.errorhandler(500)
def internal_error(exc):
    return error_response('An unexpected error occurred. Check server logs using the request ID.', 500)


@app.route('/healthz')
def health():
    bank = load_bank()
    conn = rundb._connect()
    try:
        conn.execute('SELECT COUNT(*) FROM runs').fetchone()
    finally:
        conn.close()
    return jsonify(status='ok', questions=len(bank['problems']))


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
    query = request.args.get('q', '').strip()
    if len(query) > 100:
        abort(400, description='Search must be at most 100 characters.')
    for value, allowed in ((topic, topics), (diff, difficulties), (category, categories)):
        if value and value not in allowed:
            abort(400, description='Invalid question filter.')
    if query:
        problems = [p for p in problems if query.casefold() in
                    f"{p['id']} {p['title']} {p['topic']}".casefold()]
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
        selected_query=query,
    )


@app.route("/question/<problem_id>")
def question(problem_id):
    bank = load_bank()
    problem = next((p for p in bank["problems"] if p["id"] == problem_id), None)
    if problem is None:
        abort(404, description='Question not found.')
    return render_template("question.html", p=problem)


@app.route("/run-tests")
def run_tests_page():
    return render_template("run_tests.html", runner_enabled=bool(app.config['RUNNER_TOKEN']))


@app.route("/analytics")
def analytics():
    bank = load_bank()
    stats = rundb.get_analytics(bank["problems"])
    runs  = rundb.get_runs(limit=20)
    return render_template("analytics.html", stats=stats, runs=runs)


# ── test runner APIs ──────────────────────────────────────────────────────────

@app.route("/api/run-python-tests", methods=["POST"])
def api_run_python():
    return _run_suite('python')


@app.route("/api/run-sql-tests", methods=["POST"])
def api_run_sql():
    return _run_suite('sql')


@app.route("/api/run-cpp-tests", methods=["POST"])
def api_run_cpp():
    return _run_suite('cpp')


@app.route('/api/run-adversarial-tests', methods=['POST'])
def api_run_adversarial():
    return _run_suite('adversarial')


def csv_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


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
        writer.writerow({key: csv_safe(value) for key, value in dict(r).items()})
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=case_results.csv"},
    )


if __name__ == "__main__":
    app.run(host='127.0.0.1', debug=False, port=5000)
