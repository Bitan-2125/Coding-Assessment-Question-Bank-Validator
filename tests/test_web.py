import pathlib
import tempfile
import unittest
from unittest.mock import patch

from web.app import app, RUN_LOCK
from web import db


class WebTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_config = {key: app.config[key] for key in ('TESTING', 'DATABASE_PATH', 'RUNNER_TOKEN')}
        app.config.update(TESTING=True, DATABASE_PATH=str(pathlib.Path(self.directory.name) / 'history.db'),
                          RUNNER_TOKEN='test-only-token')
        self.client = app.test_client()
        self.headers = {'X-Runner-Token':'test-only-token'}

    def tearDown(self):
        app.config.update(self.old_config)
        self.directory.cleanup()

    def test_pages_filters_and_all_questions_render(self):
        for url in ('/', '/run-tests', '/analytics', '/healthz', '/export/runs.csv', '/export/case-results.csv'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        from validation import load_bank
        for problem in load_bank()['problems']:
            self.assertEqual(self.client.get('/question/' + problem['id']).status_code, 200)
        response = self.client.get('/?q=two+sum')
        self.assertIn(b'Two Sum', response.data)
        self.assertNotIn(b'Valid Anagram', response.data)
        for url in ('/?category=invalid', '/?difficulty=invalid', '/?q=' + 'x'*101):
            self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(self.client.get('/question/missing').status_code, 404)

    def test_no_token_exposure_and_security_headers(self):
        response = self.client.get('/run-tests')
        self.assertNotIn(b'test-only-token', response.data)
        for header in ('X-Request-ID', 'Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options'):
            self.assertIn(header, response.headers)
        self.assertFalse(app.debug)
        self.assertEqual(self.client.get('/', headers={'Host':'attacker.example'}).status_code, 400)

    def test_execution_authorization_and_request_validation(self):
        url = '/api/run-python-tests'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 401)
        self.assertEqual(self.client.post(url, headers={**self.headers, 'Origin':'https://attacker.example'}).status_code, 403)
        self.assertEqual(self.client.post(url, headers=self.headers, json={'candidate':'x'}).status_code, 400)
        app.config['RUNNER_TOKEN'] = ''
        self.assertEqual(self.client.post(url, headers=self.headers).status_code, 503)

    def test_busy_runner(self):
        RUN_LOCK.acquire()
        try:
            response = self.client.post('/api/run-python-tests', headers=self.headers)
            self.assertEqual(response.status_code, 409)
        finally:
            RUN_LOCK.release()

    def test_real_web_runner_database_analytics_export_flow(self):
        for suite, expected in (('python', 104), ('sql', 30), ('cpp', 48), ('adversarial', 1)):
            response = self.client.post(f'/api/run-{suite}-tests', headers=self.headers)
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json['status'], 'passed')
            self.assertGreaterEqual(response.json['passed'], expected)
            self.assertGreater(response.json['run_id'], 0)
        with app.app_context():
            runs = db.get_runs()
            self.assertEqual(len(runs), 4)
            self.assertEqual(next(r for r in runs if r['suite'] == 'sql')['passed'], 30)
        response = self.client.get('/analytics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Failed runs: 0', response.data)
        self.assertIn(b'SQL001', self.client.get('/export/case-results.csv').data)

    def test_timeout_is_recorded_and_lock_is_released(self):
        result = dict(status='timeout', exit_code=124, output='Deadline exceeded',
                      passed=0, failed=0, skipped=0, duration_seconds=30, suite='python')
        with patch('web.app.execute', return_value=result):
            response = self.client.post('/api/run-python-tests', headers=self.headers)
        self.assertEqual(response.status_code, 504)
        self.assertFalse(RUN_LOCK.locked())
        with app.app_context():
            self.assertEqual(db.get_analytics([])['failed_runs'], 1)

    def test_storage_failure_does_not_claim_persistence(self):
        import sqlite3
        result = dict(status='passed', exit_code=0, output='Result: 1 passed, 0 failed')
        with patch('web.app.execute', return_value=result), patch('web.db.record_run', side_effect=sqlite3.OperationalError('private-path')):
            response = self.client.post('/api/run-python-tests', headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private-path', response.json['error'])
        self.assertFalse(RUN_LOCK.locked())

    def test_csv_formula_is_escaped(self):
        with app.app_context():
            db.record_run('python', '[FAIL] DSA001 case 1: =SUM(1,2)\nResult: 0 passed, 1 failed', 1)
        response = self.client.get('/export/case-results.csv')
        self.assertIn(b"'=SUM", response.data)
