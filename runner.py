"""Allowlisted bundled suites, bounded duration, stable result envelope."""
import argparse
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent
SUITES = {
    'python': ('run_python_tests.py', 30),
    'sql': ('run_sql_tests.py', 90),
    'cpp': ('run_cpp_tests.py', 150),
    'adversarial': ('run_adversarial_tests.py', 120),
}
LOG = logging.getLogger(__name__)


def execute(suite):
    if suite not in SUITES:
        raise ValueError('Unknown test suite')
    script, timeout = SUITES[suite]
    return execute_command(suite, [sys.executable, str(ROOT / 'tests' / script)], timeout)


def execute_command(suite, command, timeout):
    started = time.monotonic()
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    status = 'failed'
    exit_code = 1
    # Disk capture avoids retaining unrestricted output in server memory.
    with tempfile.TemporaryFile() as output_file:
        try:
            process = subprocess.run(command, cwd=ROOT, stdout=output_file,
                                     stderr=subprocess.STDOUT, timeout=timeout, env=env)
            exit_code = process.returncode
            status = 'passed' if exit_code == 0 else 'failed'
        except subprocess.TimeoutExpired:
            status, exit_code = 'timeout', 124
        except OSError as exc:
            status, exit_code = 'error', 127
            output_file.write(f'Runner could not start: {type(exc).__name__}\n'.encode())
        output_file.seek(0)
        raw = output_file.read(256_001)
    truncated = len(raw) > 256_000
    output = raw[:256_000].decode('utf-8', errors='replace').replace('\r\n', '\n')
    if truncated:
        output += '\n[ERROR] Output exceeded reporting limit; run is incomplete.\n'
        status, exit_code = 'error', 1
    if status == 'timeout':
        output += f'\n[ERROR] Suite exceeded {timeout} seconds.\n'
    summary = re.search(r'Result:\s*(\d+) passed,\s*(\d+) failed(?:,\s*(\d+) skipped)?', output)
    counts = {'passed': 0, 'failed': 0, 'skipped': 0}
    if summary:
        counts = dict(zip(counts, (int(v or 0) for v in summary.groups())))
    elif suite == 'regression':
        match = re.search(r'Ran (\d+) tests?', output)
        if match and status == 'passed' and re.search(r'^OK\s*$', output, re.MULTILINE):
            counts['passed'] = int(match.group(1))
        elif status == 'passed':
            status, exit_code = 'error', 1
            output += '\n[ERROR] Regression tests did not finish with an unqualified OK.\n'
    # A suite cannot be green just because its process exited with code zero.
    if suite in SUITES and status == 'passed' and (
        not summary or counts['passed'] == 0 or counts['failed'] or counts['skipped']
    ):
        status, exit_code = 'error', 1
        output += '\n[ERROR] Missing, empty or incomplete successful test summary.\n'
    result = dict(suite=suite, status=status, exit_code=exit_code, output=output,
                  duration_seconds=round(time.monotonic() - started, 3), **counts)
    LOG.info('suite=%s status=%s exit_code=%s duration=%.3f', suite, status,
             exit_code, result['duration_seconds'])
    return result


def main():
    parser = argparse.ArgumentParser(description='Run all validation and regression suites')
    parser.add_argument('--report', type=pathlib.Path, default=ROOT / 'reports' / 'verification.json')
    args = parser.parse_args()
    results = [execute_command('regression', [sys.executable, '-m', 'unittest',
               'discover', '-s', 'tests', '-p', 'test_*.py', '-v'], 120)]
    results.extend(execute(suite) for suite in SUITES)
    for result in results:
        print(f"\n=== {result['suite']}: {result['status']} ===\n{result['output']}")
    report = {'success': all(r['status'] == 'passed' for r in results), 'results': results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Report: {args.report}')
    return int(not report['success'])


if __name__ == '__main__':
    sys.exit(main())
