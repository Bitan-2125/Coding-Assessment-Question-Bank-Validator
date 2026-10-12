"""
SQL result comparator.
Loads schema.sql into an in-memory SQLite DB, runs each reference query,
then runs the candidate query and compares result sets.

Usage (from project root):
    python tests/run_sql_tests.py [candidate_queries.sql]

If no candidate file is given, it runs the reference queries against
themselves (self-test mode).

Candidate SQL file format:
    -- SQL001
    SELECT ...;
    -- SQL002
    SELECT ...;
    ...

Lines starting with '--' that match 'SQL[0-9]+' are used as section headers.
"""

import pathlib
import re
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "schema.sql"

# Reference queries extracted directly — keeps the test runner self-contained.
REFERENCE_QUERIES: dict[str, str] = {
    "SQL001": """
        SELECT c.customer_id, c.name
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.order_id IS NULL
        ORDER BY c.customer_id
    """,
    "SQL002": """
        SELECT c.region, SUM(o.amount) AS revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        GROUP BY c.region
        HAVING SUM(o.amount) > 1000
        ORDER BY revenue DESC
    """,
    "SQL003": """
        SELECT MAX(salary) AS second_highest_salary
        FROM employees
        WHERE salary < (SELECT MAX(salary) FROM employees)
    """,
    "SQL004": """
        WITH ranked AS (
            SELECT e.*,
                   DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rnk
            FROM employees e
        )
        SELECT employee_id, name, department_id, salary
        FROM ranked WHERE rnk = 1
        ORDER BY department_id, employee_id
    """,
    "SQL005": """
        SELECT strftime('%Y-%m', order_date) AS month, SUM(amount) AS revenue
        FROM orders
        WHERE amount IS NOT NULL
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month
    """,
    "SQL006": """
        SELECT email
        FROM users
        WHERE email IS NOT NULL
        GROUP BY email
        HAVING COUNT(*) > 1
        ORDER BY email
    """,
    "SQL007": """
        SELECT c.customer_id, c.name
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        HAVING COUNT(o.order_id) >= 3
        ORDER BY c.customer_id
    """,
    "SQL008": """
        SELECT transaction_id, account_id, transaction_date, amount,
               SUM(amount) OVER (
                   PARTITION BY account_id
                   ORDER BY transaction_date, transaction_id
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) AS running_balance
        FROM transactions
        ORDER BY account_id, transaction_date, transaction_id
    """,
    "SQL009": """
        SELECT p.product_id, p.name
        FROM products p
        WHERE NOT EXISTS (
            SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id
        )
        ORDER BY p.product_id
    """,
    "SQL010": """
        SELECT date(event_time) AS event_date, COUNT(DISTINCT user_id) AS active_users
        FROM events
        WHERE user_id IS NOT NULL
        GROUP BY date(event_time)
        ORDER BY event_date
    """,
}

# Problems where row order matters (ORDER BY is deterministic and part of spec)
ORDER_SENSITIVE = {"SQL004", "SQL008"}


def make_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    return conn


def run_query(conn: sqlite3.Connection, sql: str):
    try:
        cur = conn.execute(sql)
        return cur.fetchall(), None
    except sqlite3.Error as e:
        return None, str(e)


def rows_equal(ref_rows, cand_rows, problem_id: str) -> bool:
    if problem_id in ORDER_SENSITIVE:
        return ref_rows == cand_rows
    # Order-insensitive: sort both
    return sorted(ref_rows) == sorted(cand_rows)


def parse_candidate_file(path: pathlib.Path) -> dict[str, str]:
    """Parse a candidate SQL file into {problem_id: query} dict."""
    queries: dict[str, str] = {}
    current_id = None
    buf: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"--\s*(SQL\d+)", line, re.IGNORECASE)
        if m:
            if current_id and buf:
                queries[current_id] = "\n".join(buf).strip()
            current_id = m.group(1).upper()
            buf = []
        else:
            if current_id is not None:
                buf.append(line)

    if current_id and buf:
        queries[current_id] = "\n".join(buf).strip()

    return queries


def main():
    if len(sys.argv) > 1:
        candidate_path = pathlib.Path(sys.argv[1])
        if not candidate_path.exists():
            print(f"Candidate file not found: {candidate_path}")
            sys.exit(1)
        candidate_queries = parse_candidate_file(candidate_path)
        mode = f"candidate: {candidate_path.name}"
    else:
        # self-test: run reference queries as both reference and candidate
        candidate_queries = dict(REFERENCE_QUERIES)
        mode = "self-test (reference vs reference)"

    print(f"SQL validator — {mode}\n")

    conn = make_db()
    passed = failed = skipped = 0

    for pid, ref_sql in sorted(REFERENCE_QUERIES.items()):
        if pid not in candidate_queries:
            print(f"[SKIP]  {pid}: no query provided")
            skipped += 1
            continue

        cand_sql = candidate_queries[pid]

        ref_rows, ref_err = run_query(conn, ref_sql)
        if ref_err:
            print(f"[ERROR] {pid}: reference query failed — {ref_err}")
            failed += 1
            continue

        cand_rows, cand_err = run_query(conn, cand_sql)
        if cand_err:
            print(f"[FAIL]  {pid}: candidate query error — {cand_err}")
            failed += 1
            continue

        if rows_equal(ref_rows, cand_rows, pid):
            passed += 1
            print(f"[PASS]  {pid}")
        else:
            failed += 1
            print(f"[FAIL]  {pid}: result mismatch")
            print(f"        reference  ({len(ref_rows)} rows): {ref_rows[:3]}{'...' if len(ref_rows)>3 else ''}")
            print(f"        candidate  ({len(cand_rows)} rows): {cand_rows[:3]}{'...' if len(cand_rows)>3 else ''}")

    conn.close()
    print(f"\nResult: {passed} passed, {failed} failed, {skipped} skipped")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
