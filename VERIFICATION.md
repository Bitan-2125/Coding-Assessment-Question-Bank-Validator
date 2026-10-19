# Verification record — 2026-10-19

## Final result

`python runner.py` exited successfully in the project's virtual environment.
Machine-readable report: `reports/verification.json`. Captured console log:
`reports/final-verification.log`. Reports are generated local artifacts;
this document records the handover result.

| Suite | Final observed result |
| --- | --- |
| Infrastructure/web regression | 27 tests passed |
| Python reference cases + examples | 104 passed, 0 failed |
| SQL reference fixtures | 30 passed, 0 failed |
| C++ reference cases | 48 passed, 0 failed |
| Hypothesis/adversarial | 3,432 checks passed, 0 failed |
| Dependency consistency (`pip check`) | No broken requirements |

Hypothesis check counts vary by generated data. Regression tests separately
execute all four real web runner endpoints against a temporary SQLite database;
those checks are not added to the standalone reference totals above.

Environment: local Windows, Python 3.13.3, Flask 3.1.3, Waitress 3.0.2,
Hypothesis 6.170.2 and the installed g++ C++17 toolchain. Requirements pin
verified package versions. Linux/Python 3.11 CI is configured but not executed
in this environment.

## Reviewable stage evidence

1. **Baseline:** original Python 77/77, C++ 41/41, SQL 10/10. SQL compared
   references with themselves. Hypothesis failed to import; Flask and Waitress
   were also absent. Installed dependencies in `.venv` after network approval.
2. **Stage 1 — validation:** five regression tests passed. Python 97 included
   20 examples; SQL expanded to 30 independent fixture checks; C++ retained 41
   passing cases; Hypothesis completed 3,486 checks after installation.
3. **Stage 2 — execution/history:** 15 regression tests and all four standalone
   suites passed (`reports/stage2.json`). Added failures for incomplete SQL,
   compiler/timeouts, false success, and unsafe query operations, plus honest
   failed-run analytics. The timeout regression intentionally emits a C++
   `[ERROR]` line; that is expected evidence, not a failed suite.
4. **Stage 3 — web/edge cases:** first run found a Unicode fixture corrupted by
   PowerShell stdin encoding and an invalid-host error template calling URL
   generation without a routing adapter. Fixed the fixture using Unicode escapes
   in ASCII source, and used a static stylesheet path. Rerun passed 23 regression
   tests, Python 104, SQL 30, C++ 48 and 3,506 generated checks (`reports/stage3.json`).
5. **Stage 4 — delivery:** an initial run failed because a new grid type check
   rejected the existing supported `list[str]` example. Expanded the contract to
   accept both string rows and lists of characters, retaining rectangular/binary
   cell checks. Added rollback, output-limit, alternate-answer and external-C++
   acknowledgement checks. Final results are above. Documented Waitress proxy
   CLI arguments were accepted by the installed parser; TLS proxy integration
   was not deployed or tested.

The existing Git repository is in the inner project directory. The initial
assessment incorrectly reported no Git repository because checks ran from its
parent. Implementation stages are described here and in IMPLEMENTATION_PLAN.md;
the GitHub delivery preserves the upstream README repository URL correction.

## Browser → API → storage → UI

Story: an operator searches the bank, runs bundled reference validation, then
reviews persisted analytics and exports case results.

| Boundary | Observed evidence |
| --- | --- |
| Server startup | Waitress logged `Serving on http://127.0.0.1:8080` |
| Search UI | Entered “two sum”; heading changed from Questions 30 to Questions 1 |
| Browser → API | Clicked SQL Run with temporary token; buttons disabled while running |
| API → SQLite | Run #1 stored with case rows in a separate demo database |
| Response → UI | PASSED, 30 passed, 0 failed, 0.202s, Run #1 |
| Analytics | One run, 30 passed, zero failed; SQL coverage shown by topic |
| Export | Browser downloaded case_results.csv |
| Diagnostics | No browser warning/error entries observed during the flow |

Browser flow used `reports/browser-demo.db`, separate from normal history.
Screenshot: `reports/browser-analytics.jpg`. All 30 question pages, empty-history
analytics and both CSV routes also rendered in Flask client tests. Automated
tests verified real Python/SQL/C++/adversarial web execution and persistence
using temporary databases.

## Tested failures and edge cases

- Malformed/duplicate-key/nonfinite JSON, wrong counts, duplicate IDs, unknown
  references, missing expectations, argument types/shapes and SQL fixtures.
- Boolean versus integer confusion, group duplicates, valid alternative answers
  and case input mutation isolation.
- Incomplete/duplicate/unknown SQL sections; write, attach, pragma, extension,
  recursive work and row-limit restrictions.
- Compiler/compile/case/outer-runner failures and deadlines; missing success
  summary, oversized output and suite traversal attempts.
- Unauthorized, wrong-method, cross-origin or body-bearing execution; disabled
  runner, invalid host/filter, busy runner and token non-disclosure in HTML.
- Case parsing, false top-failure rows, transaction rollback, infrastructure
  failure history, storage errors and CSV formula escaping.
- C++ Unicode/surrogate JSON, escaped characters, 32-bit complement overflow,
  products above 32 bits, multiple zeros and repeated matching indices.

## Not verified / remaining work

No remote deployment, hosted CI run, TLS/proxy integration, service-manager
installation, backup/restore drill, mobile-device audit, formal accessibility
audit, penetration test or load benchmark was performed. The screenshot is a
desktop viewport, not mobile certification. Tests do not prove every prose
constraint or all possible solutions. Security limits, single-process scope
and absence of an untrusted-code sandbox are documented in README.md and
DEPLOYMENT.md.
