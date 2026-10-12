# Coding Assessment Question Bank & Validator

A self-contained coding assessment platform built for practice, portfolio demonstration, and candidate evaluation. It includes **30 original problems** across Data Structures & Algorithms and SQL, each with a full problem statement, constraints, sample I/O, reference solution, complexity analysis, and documented failure modes.

Beyond the question bank, the project includes automated validators for Python, C++17, and SQL submissions, so solutions are actually executed and checked — not just written and forgotten. A lightweight Flask web interface lets you browse and filter problems, run all test suites from the browser, and view an analytics dashboard showing pass rates by topic and difficulty. Every test run is stored in a local SQLite database and can be exported to CSV for further analysis in Excel or Google Sheets.

Built as a portfolio project for a data analytics / outcome-based learning role — it demonstrates structured problem design, test automation, result tracking, and data visualisation in a single cohesive tool.

---

## Features

- 30 structured problems — each with difficulty, topic, constraints, sample I/O, reference solution, complexity analysis, and common pitfalls
- Automated validators for Python, C++17, and SQL submissions
- 3500+ property-based and adversarial edge-case tests via Hypothesis
- Web UI to browse, filter, and view questions
- Analytics dashboard with Chart.js charts — pass rate by difficulty, topic, and category, plus run trend over time
- CSV export of all test run history for further analysis in Excel / Google Sheets

---

## Project Structure

```
coding_assessment_bank/
├── question_bank.json          # All 30 problems — metadata, test cases, complexity notes
├── python/
│   └── reference_solutions.py  # Python reference implementations (DSA001–DSA020)
├── cpp/
│   ├── reference_solutions.cpp # C++17 reference implementations (10 core problems)
│   └── harness.cpp             # I/O harness for compiling and testing C++ submissions
├── sql/
│   ├── schema.sql              # SQLite-compatible schema + sample dataset
│   └── questions_and_solutions.md  # 10 SQL problems with reference queries and pitfalls
├── tests/
│   ├── run_python_tests.py     # Validates Python solutions against question_bank.json
│   ├── run_cpp_tests.py        # Compiles and validates C++ submissions
│   ├── run_sql_tests.py        # Runs SQL queries and compares result sets
│   └── run_adversarial_tests.py  # 3500+ randomized + edge-case tests via Hypothesis
├── web/
│   ├── app.py                  # Flask web application
│   ├── db.py                   # SQLite run history store
│   ├── templates/              # Jinja2 HTML templates
│   └── static/style.css        # Dark-theme stylesheet
└── reports/
    └── runs.db                 # Auto-created — stores all test run history
```

---

## Requirements

| Tool | Version | Used for |
|---|---|---|
| Python | 3.9+ | All validators and the web app |
| Flask | Any recent | Web interface |
| Hypothesis | Any recent | Adversarial tests |
| g++ | C++17 support | C++ validator |
| SQLite | Built into Python | SQL validator + run history |

---

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/Bitan-2125/Coding-Assessment-Question-Bank-Validator.git
cd Coding-Assessment-Question-Bank-Validator
```

**2. Create and activate a virtual environment**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install flask hypothesis
```

> `g++` is only needed for the C++ validator. On Windows install [MinGW](https://www.mingw-w64.org/), on macOS run `xcode-select --install`, on Linux run `sudo apt install g++`.

---

## Usage

### Run the web interface

```bash
python web/app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

From the web UI you can:
- Browse all 30 questions and filter by category, difficulty, or topic
- Click any question to view the full problem statement, constraints, test cases, and complexity notes
- Go to **Run Tests** to execute any of the three validators and see live output
- Go to **Analytics** to view charts and download CSV exports

---

### Run validators from the command line

All commands should be run from the project root (`coding_assessment_bank/`).

**Python validator** — no extra dependencies

```bash
python tests/run_python_tests.py
```

Expected output:
```
[PASS] DSA001 case 1
[PASS] DSA001 case 2
...
Result: 77 passed, 0 failed
```

---

**SQL validator** — uses in-memory SQLite, no extra dependencies

```bash
# Self-test: runs reference queries against themselves
python tests/run_sql_tests.py

# Validate a candidate SQL file
python tests/run_sql_tests.py path/to/candidate_queries.sql
```

Candidate SQL file format — label each query with a comment header matching the problem ID:

```sql
-- SQL001
SELECT c.customer_id, c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- SQL002
SELECT c.region, SUM(o.amount) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.region
HAVING SUM(o.amount) > 1000;
```

---

**C++ validator** — requires `g++` on PATH

```bash
# Self-test: uses cpp/reference_solutions.cpp
python tests/run_cpp_tests.py

# Validate a candidate C++ file
python tests/run_cpp_tests.py path/to/candidate.cpp
```

The candidate file must implement the same function signatures as `cpp/reference_solutions.cpp`. The harness handles all I/O automatically — no `main()` needed in the candidate file.

Supported problems: `DSA001 DSA002 DSA005 DSA007 DSA008 DSA009 DSA010 DSA012 DSA014 DSA020`

---

**Adversarial + property-based tests**

```bash
python tests/run_adversarial_tests.py
```

Runs 3500+ randomized and edge-case checks across core DSA solutions using [Hypothesis](https://hypothesis.readthedocs.io/). Covers empty inputs, duplicates, all-negative values, max constraints, and brute-force verified random cases.

---

## Analytics & CSV Export

Every test run triggered from the web UI (or directly via the API) is stored in `reports/runs.db`.

Go to [http://127.0.0.1:5000/analytics](http://127.0.0.1:5000/analytics) to see:

- Summary cards — total questions, runs, cases passed/failed
- Pass rate by difficulty (Easy / Medium / Hard)
- Pass rate by category (DSA / SQL)
- Pass rate by topic (stacked bar)
- Test run trend over time (line chart)
- Top failing problems table

Download raw data:
- [/export/runs.csv](http://127.0.0.1:5000/export/runs.csv) — one row per suite run
- [/export/case-results.csv](http://127.0.0.1:5000/export/case-results.csv) — one row per individual test case result

---

## Problem List

### DSA Problems

| ID | Title | Topic | Difficulty |
|---|---|---|---|
| DSA001 | Two Sum | Arrays / Hashing | Easy |
| DSA002 | Valid Anagram | Strings / Hashing | Easy |
| DSA003 | First Non-Repeating Character | Strings / Hashing | Easy |
| DSA004 | Move Zeroes | Arrays / Two Pointers | Easy |
| DSA005 | Binary Search | Binary Search | Easy |
| DSA006 | Merge Sorted Arrays | Arrays / Two Pointers | Easy |
| DSA007 | Maximum Subarray Sum | Arrays / Kadane | Medium |
| DSA008 | Best Time to Buy and Sell Stock | Arrays / Greedy | Easy |
| DSA009 | Longest Substring Without Repeats | Strings / Sliding Window | Medium |
| DSA010 | Balanced Brackets | Stack | Easy |
| DSA011 | Top K Frequent Elements | Hashing / Heap | Medium |
| DSA012 | Product Except Self | Arrays / Prefix-Suffix | Medium |
| DSA013 | Rotate Array Right | Arrays | Easy |
| DSA014 | Missing Number | Arrays / Math | Easy |
| DSA015 | Group Anagrams | Hashing / Strings | Medium |
| DSA016 | Number of Islands | Graphs / DFS | Medium |
| DSA017 | Shortest Path in Unweighted Graph | Graphs / BFS | Medium |
| DSA018 | Climbing Stairs | Dynamic Programming | Easy |
| DSA019 | Coin Change Minimum | Dynamic Programming | Medium |
| DSA020 | Merge Overlapping Intervals | Sorting / Intervals | Medium |

### SQL Problems

| ID | Title | Topic | Difficulty |
|---|---|---|---|
| SQL001 | Customers Without Orders | Aggregation / Join | Easy |
| SQL002 | Revenue by Region | GROUP BY / HAVING | Easy |
| SQL003 | Second Highest Salary | Subquery | Easy |
| SQL004 | Top Employee per Department | Window Functions | Medium |
| SQL005 | Monthly Revenue | Date / DISTINCT | Easy |
| SQL006 | Duplicate Emails | GROUP BY / HAVING | Easy |
| SQL007 | Customers With At Least Three Orders | Aggregation / Join | Easy |
| SQL008 | Running Account Balance | Window Functions | Medium |
| SQL009 | Products Never Sold | Subquery / Join | Medium |
| SQL010 | Daily Active Users | Date / DISTINCT | Medium |

---

## How the C++ Harness Works

The harness (`cpp/harness.cpp`) is compiled together with the candidate's solution. It reads JSON lines from stdin in the format:

```json
{"problem":"DSA001","args":[[2,7,11,15],9]}
```

And writes the result as JSON to stdout:

```json
[0,1]
```

The Python runner (`run_cpp_tests.py`) generates these lines from `question_bank.json`, feeds them to the compiled binary, and diffs the output against the expected values.

---

## Notes

- The validators test **reference implementations** — this is not a sandboxed online judge. Do not run untrusted candidate code without additional isolation.
- SQL tests use an in-memory SQLite database seeded from `sql/schema.sql`. Queries using non-SQLite syntax (e.g. `ISNULL`, `TOP`) will fail.
- The C++ harness currently supports 10 of the 20 DSA problems. Remaining problems can be added by extending the dispatcher in `cpp/harness.cpp`.
- Run history persists in `reports/runs.db` across app restarts. Delete this file to reset analytics.
