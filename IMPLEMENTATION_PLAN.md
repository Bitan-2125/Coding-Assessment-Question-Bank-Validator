# Client preparation plan

## Architecture and baseline

Inspected all source, data, templates, styles, SQL and C++ assets. The project
uses a JSON question bank, Python reference functions, a C++ line-protocol
harness, standalone validator scripts, Flask/Jinja pages, and SQLite history.
The baseline lacked a dependency manifest, CI, and infrastructure test suite.
The Git repository is in the inner project directory; the initial Git check
incorrectly ran from its parent.
Keep this architecture and working algorithms.

Baseline on 2026-10-19: Python 77/77; C++ 41/41; SQL 10/10 (reference compared
with itself, so not independent correctness evidence). Adversarial suite could
not start: Hypothesis missing. Flask and Waitress also missing.

## Prioritized stages

1. **P0 — trustworthy validation:** explicit JSON structure and reference binding
   checks; strict result comparison; isolated case inputs; independent SQL
   expectations on normal, empty and edge datasets; regression tests.
2. **P0 — reliable execution:** missing/incomplete submissions fail; compiler and
   execution deadlines; SQL read-only authorizer, operation/row limits; one suite
   command with machine-readable report and honest failure propagation; history
   regression tests and correct zero-failure analytics.
3. **P0/P1 — web and security:** retain Flask pages; improve search, accessibility,
   status and errors; bundled references only; execution token, same-origin
   protection, bounded concurrency, safe error responses, debug off, health probe.
4. **P1 — delivery:** versioned dependencies, production WSGI entry point, CI,
   configuration/logging, setup/deployment guide and client demonstration.

## Acceptance and boundaries

Run regression tests and relevant existing suites after each stage; record
failures and final checks in VERIFICATION.md. Verify the web-to-runner-to-database
flow using temporary databases. Do not claim browser visual review or live
deployment unless performed. No public arbitrary-code execution: C++ candidate
execution remains a trusted-local CLI operation with explicit opt-in. Process
timeouts and SQL restrictions are not an OS sandbox. Authentication at the
reverse proxy is required for shared deployments.

## Completion

All four stages are complete for the trusted-reference scope. Final results:
27 regression tests, 104 Python checks, 30 SQL checks, 48 C++ checks and 3,432
generated checks in the final run. The local Waitress browser flow was exercised.
See VERIFICATION.md for failures, fixes and delivery verification boundaries.
