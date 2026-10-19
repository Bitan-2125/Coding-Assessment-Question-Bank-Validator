# Prospective-client demo (about 3 minutes)

## Preparation

Install requirements-dev.txt and g++, then run `python runner.py`. Open the
latest `reports/verification.json` and confirm `success: true`. Start with an
empty **demo-only** history file so results are easy to explain:

```powershell
$env:ASSESSMENT_DB = Join-Path $PWD 'reports/client-demo.db'
$env:ASSESSMENT_RUNNER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python serve.py
```

Keep the token off the recording; paste it into the masked field before
screen-sharing that page. Reusing the demo DB retains previous results.
Use a new filename if a clean run is needed. No production history is reset.

## Script

**0:00 — Problem and scope.**
“This tool helps review a coding question bank before it reaches candidates.
It checks that the bank is structured correctly and that bundled reference
answers match its examples and test expectations.”

**0:20 — Browse and inspect.**
Open http://127.0.0.1:8080. Search “two sum”, open DSA001, and show the
statement, constraints, example and test cases. Explain that multiple valid
index pairs are accepted. Clear search and filter to SQL. Open SQL004 and
show the reference query and fixtures, including ties and empty data.

**1:00 — Run and explain evidence.**
Open Run Tests. Enter the runner token. Run Python and SQL sequentially.
“Each run shows pass/fail details, counts, duration and a persisted run ID.
SQL checks use independent expected rows across three datasets, so a query
is not simply compared against itself.”
Expect 104 Python checks and 30 SQL checks for the delivered bank. Optionally
run C++ (48 checks) and the property suite (variable generated count).
Do not promise that runtime or random-test counts will be identical elsewhere.

**1:50 — Analytics and export.**
Open Analytics. Show recent runs, the topic table and historical totals.
Download case_results.csv. “These are observed results across recorded runs,
not a proof of correctness or a measure of candidate skill.”

**2:20 — Failure reporting.**
Clear the token field and attempt a run: the page explains that a token is
required. For a technical audience, show VERIFICATION.md: tests cover incomplete
SQL submissions, invalid formats, deadlines, busy runners and storage errors.
Do not introduce a deliberate defect into the working demo bank.

**2:45 — Delivery boundary.**
“This version is intended for a trusted team validating reference solutions.
It includes setup, deployment instructions and repeatable verification. A
public candidate-code platform would be a separate phase with sandboxed
workers, user roles and a durable job queue.”

## Close

Offer to review the client's question formats, evaluation rules and hosting
constraints. Show README.md, DEPLOYMENT.md and the latest verification report.
Do not describe external hosting, load capacity or security audits as completed.
