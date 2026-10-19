# Coding Assessment Question Bank Validator

A Flask application and command-line validators for 30 coding questions:
20 Python algorithm references, 10 C++ implementations, and 10 SQLite queries.
The existing Flask/Jinja/SQLite architecture is retained. This delivery adds
validation contracts, independent SQL fixtures, reliable execution/reporting,
web protections, regression tests, and an operational handover.

## Setup (Windows PowerShell)

For a fresh checkout:

```powershell
git clone https://github.com/Bitan-2125/Coding-Assessment-Question-Bank-Validator.git
cd Coding-Assessment-Question-Bank-Validator
```

For the existing local copy, the repository root is
`D:\coding_assessment_bank\coding_assessment_bank`. Run the following from
the repository root (after cloning, you are already there):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python runner.py
```

If PowerShell activation is unavailable, use `.\.venv\Scripts\python.exe`
in place of `python`; no execution-policy change is needed.
Python 3.11+ is the supported target; locally verified on Python 3.13.3.
A C++17 `g++` compiler on PATH is required for the full verification command.
Missing dependencies/compiler produce failures, not a false all-pass.
On Linux/macOS activate with `source .venv/bin/activate`; the Python commands
are otherwise the same. Other platforms have CI configuration but have not
been exercised locally.

Generate a private runner token and start the production server:

```powershell
$env:ASSESSMENT_RUNNER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python serve.py
```

Open [the application](http://127.0.0.1:8080). In the same local terminal,
`$env:ASSESSMENT_RUNNER_TOKEN` shows the value to paste into the Runner token
field. Do not share that value in screenshots or recordings. The field is
masked and the browser does not persist it. Without a token, browsing works
and test execution returns 503. Stop the server with Ctrl+C.

## Completed features

- Question browsing, title/ID/topic search, validated category/difficulty/topic
  filters, detail pages, examples, reference identifiers/SQL and expected cases.
- Bank structure, unique IDs/JSON keys, count, metadata, argument signatures,
  core input types/safety domains and reference allowlist checks. Non-finite
  JSON values and banks above 5 MB are rejected.
- Python validation of all bank cases and all 20 published examples. Mutable
  input data is copied between calls. Boolean/integer confusion is rejected.
- Valid alternative answers accepted for Two Sum and Binary Search; anagram
  groups are compared without relying on group order, preserving duplicates.
- SQL expectations maintained independently in the bank: sample, empty and
  edge datasets for every SQL problem. Every case gets a fresh in-memory DB.
- SQL read-only operation/function allowlists, two-second deadline, one-million
  instruction budget and 10,000-row result cap; 256 KB candidate file cap.
- C++ compiler/case deadlines and clear missing-compiler, compile, malformed
  output and process error messages; Unicode JSON escape handling and codepoint
  counting; 64-bit product results and overflow-safe Two Sum lookup.
- One command runs regressions plus Python, SQL, C++ and Hypothesis suites,
  returns a failing exit code on any failed suite and writes a JSON report.
- Web execution accepts only bundled suites, requires a runner token, rejects
  cross-origin/body-bearing requests and allows one active suite per process.
- Per-case output, suite status/counts/duration/run ID, persistent SQLite history,
  historical analytics, accessible data tables, and CSV export with formula
  escaping for text. Infrastructure failures appear as failed runs even when
  no individual case ran.
- Debug disabled, trusted host configuration, 16 KB request limit, request IDs,
  security headers, generic service errors and request/suite logs without tokens.
- Pinned runtime/dev dependencies, a Waitress production entry point, health
  probe, CI workflow, deployment guide, verification record and demo script.

## Tests and reports

```powershell
python runner.py                                # all suites, required for handover
python runner.py --report reports/check.json    # choose report destination
python -m unittest discover -s tests -p "test_*.py" -v
python tests/run_python_tests.py
python tests/run_sql_tests.py
python tests/run_cpp_tests.py
python tests/run_adversarial_tests.py
```

`reports/verification.json` contains overall success and each suite's status,
exit code, counts, output and duration. Regression counts use unittest's run
summary; property-test counts vary by generated examples and data. Console
output is returned after completion, not streamed. CLI verification does not
add runs to the production history DB. The web does.

For trusted local candidate files only:

```powershell
python tests/run_sql_tests.py path/to/queries.sql
python tests/run_cpp_tests.py path/to/candidate.cpp --allow-unsafe-local-code
```

SQL files use exact section labels `-- SQL001` through `-- SQL010`, followed by
one query each. Duplicate/unknown sections and missing queries fail. C++ files
must implement signatures from `cpp/reference_solutions.cpp`, including
`vector<long long> productExceptSelf(const vector<int>&)`, without `main()`.
C++ supports DSA001, 002, 005, 007, 008, 009, 010, 012, 014 and 020.
There is no arbitrary Python candidate loader or web submission endpoint.

## Architecture

```text
question_bank.json             metadata, DSA cases/examples, SQL expected rows
validation.py                  bank contract and shared result comparison
runner.py                      suite allowlist, execution and JSON reports
python/reference_solutions.py  20 Python references (preserved)
cpp/                           10 C++ references and JSON-line harness
sql/schema.sql                 sample schema/data
sql/edge_fixture.sql           NULL/tie/boundary data
sql/questions_and_solutions.md editorial SQL explanations
web/app.py                     browsing, protected runner, CSV, health and errors
web/db.py                      SQLite run/case history and analytics
web/templates/, web/static/    existing Jinja interface and responsive styles
serve.py                       loopback-only single-process Waitress server
tests/                         validators and infrastructure regression tests
reports/                       local DB, generated reports/logs (ignored)
```

The bank is the executable source of truth for SQL reference queries. SQL
fixtures list `fixture` and `expected_rows`; DSA cases list `args` and exactly
one of `expected`/`expected_groups`. Update the bank, editorial SQL document,
and tests together when changing a problem. Human-readable numeric constraints
are not fully interpreted as a formal schema. Some deliberate robustness cases
exercise empty inputs outside the nominal statement bounds.

## Remaining limitations

This is a reference validator for a small trusted team/demo, not a public
sandboxed online judge. External C++ code runs with the operator's OS permissions;
the acknowledgement flag and timeouts do not contain filesystem, network,
memory, output-disk growth or child-process attacks. SQL restrictions also do
not provide OS-level isolation. Never process hostile submissions on this host.

The shared runner token authorizes execution only; it is not a user/session/role
system. Read pages and exports need a private authenticated reverse proxy in a
shared deployment. The concurrency guard covers one process. There is no durable
job queue, cancellation, distributed locking, per-user rate limit or tenant isolation.
A parent timeout may leave descendants until their own deadlines; it is not a
process-tree sandbox. Use one Waitress process and trusted bundled code only.

C++ covers half of the DSA bank. Its harness accepts generated trusted JSON,
not arbitrary malformed JSON. Integer array inputs must fit C++ `int`, product
outputs must fit signed 64-bit, and Unicode substring length counts codepoints,
not grapheme clusters. Tests are evidence on fixtures, not proof for all inputs.
The SQL function allowlist intentionally excludes unsupported SQLite features.

SQLite is for low-volume local history. Exports are capped at the latest 1,000
runs/5,000 cases; analytics aggregate repeated runs. Property tests contribute
aggregate counts but do not expose individual generated examples by topic.
Chart.js loads from a pinned external CDN URL; tables/history work offline.
The CSP allows existing inline scripts; a stricter nonce/self-hosted asset policy
is a future hardening task. No formal penetration, load or accessibility audit
has been performed. There is no license supplied; confirm commercial rights
before distribution. No external deployment has been made.

See [deployment instructions](DEPLOYMENT.md), [verification evidence](VERIFICATION.md),
[implementation plan](IMPLEMENTATION_PLAN.md) and [client demo](DEMO.md).
