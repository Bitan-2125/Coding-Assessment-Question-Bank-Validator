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
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "schema.sql"

sys.path.insert(0, str(ROOT))
from validation import BankValidationError, load_bank


def reference_queries():
    return {p['id']: p['reference_solution'] for p in load_bank()['problems'] if p['category'] == 'sql'}


# Problems where row order matters (ORDER BY is deterministic and part of spec)
ORDER_SENSITIVE = {"SQL004", "SQL008"}


def make_db(fixture="sample") -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if fixture != 'sample':
        for table in ('order_items', 'events', 'transactions', 'users', 'orders', 'employees', 'customers', 'products'):
            conn.execute(f'DELETE FROM {table}')
        if fixture == 'edge':
            conn.executescript((ROOT / 'sql' / 'edge_fixture.sql').read_text(encoding='utf-8'))
        elif fixture != 'empty':
            conn.close()
            raise ValueError('Unknown fixture')
    return conn


def run_query(conn: sqlite3.Connection, sql: str):
    # Restrict operations, not SQL text: comments and CTEs cannot bypass this.
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
               sqlite3.SQLITE_RECURSIVE}
    functions = {'sum', 'max', 'count', 'strftime', 'date', 'dense_rank', 'rank',
                 'row_number', 'coalesce', 'ifnull', 'min', 'avg', 'lower', 'upper',
                 'length', 'abs', 'round', 'trim', 'substr', 'nullif'}
    def authorize(action, arg1, arg2, database, trigger):
        if action not in allowed:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() not in functions:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    deadline = time.monotonic() + 2
    steps = 0
    def progress():
        nonlocal steps
        steps += 1000
        return int(steps > 1_000_000 or time.monotonic() > deadline)
    conn.set_authorizer(authorize)
    conn.set_progress_handler(progress, 1000)
    try:
        cur = conn.execute(sql)
        rows = cur.fetchmany(10001)
        if len(rows) > 10000:
            return None, 'Result exceeds 10000 rows'
        return rows, None
    except sqlite3.Error as e:
        return None, str(e)
    finally:
        conn.set_authorizer(None)
        conn.set_progress_handler(None, 0)


def rows_equal(ref_rows, cand_rows, problem_id: str) -> bool:
    if problem_id in ORDER_SENSITIVE:
        return ref_rows == cand_rows
    # Order-insensitive: sort both
    from collections import Counter
    return Counter(ref_rows) == Counter(cand_rows)


def parse_candidate_file(path: pathlib.Path) -> dict[str, str]:
    """Parse a candidate SQL file into {problem_id: query} dict."""
    queries: dict[str, str] = {}
    current_id = None
    buf: list[str] = []
    if path.stat().st_size > 256_000:
        raise ValueError('SQL candidate file exceeds 256 KB')

    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r"\s*--\s*(SQL\d{3})\s*", line, re.IGNORECASE)
        if m:
            if m.group(1).upper() in queries or m.group(1).upper() == current_id:
                raise ValueError(f'Duplicate SQL section: {m.group(1)}')
            if current_id:
                queries[current_id] = "\n".join(buf).strip()
            current_id = m.group(1).upper()
            if current_id not in reference_queries():
                raise ValueError(f'Unknown SQL section: {current_id}')
            buf = []
        else:
            if current_id is not None:
                buf.append(line)

    if current_id:
        queries[current_id] = "\n".join(buf).strip()

    return queries


def main():
    try:
        bank = load_bank()
        references = reference_queries()
        if len(sys.argv) > 1:
            candidate_queries = parse_candidate_file(pathlib.Path(sys.argv[1]))
            mode = 'candidate'
        else:
            candidate_queries = references
            mode = 'reference verification against independent expected rows'
    except (OSError, ValueError) as exc:
        print(f'[ERROR] SQL: {exc}')
        return 1
    print(f'SQL validator - {mode}\n')
    passed = failed = 0
    for p in bank['problems']:
        if p['category'] != 'sql':
            continue
        pid = p['id']
        if pid not in candidate_queries:
            failed += 1
            print(f'[FAIL] {pid}: no query provided')
            continue
        for i, case in enumerate(p['test_cases'], 1):
            conn = make_db(case['fixture'])
            try:
                rows, error = run_query(conn, candidate_queries[pid])
            finally:
                conn.close()
            expected = [tuple(row) for row in case['expected_rows']]
            if error or not rows_equal(expected, rows, pid):
                failed += 1
                print(f"[FAIL] {pid} case {i}: fixture={case['fixture']}; {error or f'expected={expected!r}, actual={rows!r}'}")
            else:
                passed += 1
                print(f'[PASS] {pid} case {i}')
    print(f'\nResult: {passed} passed, {failed} failed, 0 skipped')
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
