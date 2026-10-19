import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runner import execute, execute_command
from run_sql_tests import make_db, parse_candidate_file, rows_equal, run_query
from run_cpp_tests import compile_candidate, run_tests
from web import db


class SQLTests(unittest.TestCase):
    def test_readonly_restrictions_and_limits(self):
        conn = make_db()
        try:
            for sql in ('DELETE FROM customers', "ATTACH DATABASE 'elsewhere.db' AS x",
                        'PRAGMA database_list', "SELECT load_extension('bad')",
                        'SELECT randomblob(1000000)',
                        'WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT max(x) FROM n'):
                with self.subTest(sql=sql):
                    self.assertIsNotNone(run_query(conn, sql)[1])
            self.assertEqual(run_query(conn, 'SELECT COUNT(*) FROM customers'), ([(5,)], None))
            sql = 'WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<11000) SELECT x FROM n'
            self.assertIn('10000', run_query(conn, sql)[1])
        finally:
            conn.close()

    def test_comparison_handles_nulls_duplicates_and_order(self):
        self.assertTrue(rows_equal([(None,), (1,)], [(1,), (None,)], 'SQL001'))
        self.assertFalse(rows_equal([(1,), (1,)], [(1,)], 'SQL001'))
        self.assertFalse(rows_equal([(1,), (2,)], [(2,), (1,)], 'SQL008'))

    def test_duplicate_and_unknown_sections_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'candidate.sql'
            for text in ('-- SQL001\nSELECT 1;\n-- SQL001\nSELECT 2;', '-- SQL999\nSELECT 1;'):
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    parse_candidate_file(path)

    def test_missing_candidate_queries_fail_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'empty.sql'
            path.write_text('', encoding='utf-8')
            result = subprocess.run([sys.executable, 'tests/run_sql_tests.py', str(path)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)


class RunnerTests(unittest.TestCase):
    def test_unknown_suite(self):
        with self.assertRaises(ValueError):
            execute('../untrusted.py')

    def test_actual_timeout(self):
        result = execute_command('test', [sys.executable, '-c', 'import time; time.sleep(3)'], 0.1)
        self.assertEqual(result['status'], 'timeout')
        self.assertEqual(result['exit_code'], 124)

    def test_false_success_is_rejected(self):
        result = execute_command('python', [sys.executable, '-c', 'pass'], 5)
        self.assertEqual(result['status'], 'error')

    def test_output_limit_is_a_failure(self):
        result = execute_command('python', [sys.executable, '-c', 'print("x"*256001)'], 5)
        self.assertEqual(result['status'], 'error')
        self.assertNotEqual(result['exit_code'], 0)

    def test_external_cpp_requires_explicit_acknowledgement(self):
        result = subprocess.run([sys.executable, 'tests/run_cpp_tests.py', 'untrusted.cpp'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--allow-unsafe-local-code', result.stderr)

    def test_missing_compiler_and_compile_timeout(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('g++', 30)):
            with patch('run_cpp_tests.subprocess.run', side_effect=error):
                self.assertFalse(compile_candidate(pathlib.Path('x'), pathlib.Path('out'))[0])

    def test_cpp_case_timeout_is_reported(self):
        problem = {'id':'DSA001', 'test_cases':[{'args':[[1,2],3], 'expected':[0,1]}]}
        with patch('run_cpp_tests.subprocess.run', side_effect=subprocess.TimeoutExpired('exe', 2)):
            self.assertEqual(run_tests(pathlib.Path('exe'), [problem]), (0,1))


class HistoryTests(unittest.TestCase):
    def test_record_run_rolls_back_when_case_insert_fails(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as directory, patch.object(db, 'DB_PATH', pathlib.Path(directory) / 'runs.db'):
            conn = db._connect()
            conn.execute("CREATE TRIGGER reject_case BEFORE INSERT ON case_results BEGIN SELECT RAISE(ABORT, 'test failure'); END")
            conn.commit()
            conn.close()
            with self.assertRaises(sqlite3.IntegrityError):
                db.record_run('python', '[PASS] DSA001 case 1\nResult: 1 passed, 0 failed', 0)
            self.assertEqual(db.get_runs(), [])

    def test_case_parsing_and_no_false_top_failures(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, 'DB_PATH', pathlib.Path(directory) / 'runs.db'):
            run_id = db.record_run('sql', '[PASS] SQL001 case 1\nResult: 1 passed, 0 failed, 0 skipped', 0)
            self.assertGreater(run_id, 0)
            self.assertEqual(db.get_analytics([])['top_failing'], [])
            db.record_run('python', 'runner failed before cases', 127)
            self.assertEqual(db.get_analytics([])['failed_runs'], 1)
            conn = db._connect()
            try:
                self.assertEqual(conn.execute('SELECT case_num FROM case_results').fetchone()[0], 1)
            finally:
                conn.close()
