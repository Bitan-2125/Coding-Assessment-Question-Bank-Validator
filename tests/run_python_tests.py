"""Validate bundled Python references, examples and bank structure."""
import inspect
import pathlib
import sys
from copy import deepcopy

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validation import BankValidationError, REFERENCES, load_bank, results_equal, run_reference


def main():
    try:
        bank = load_bank()
    except BankValidationError as exc:
        print(f'[ERROR] BANK: {exc}')
        return 1
    passed = failed = 0
    for p in bank['problems']:
        if p['category'] != 'dsa':
            continue
        fn = REFERENCES[p['reference_solution']]
        cases = deepcopy(p['test_cases'])
        example = p['examples']
        bound = inspect.signature(fn).bind(**example['input'])
        key = 'expected_groups' if p['reference_solution'] == 'group_anagrams' else 'expected'
        cases.append({'args': list(bound.args), key: example['output']})
        for i, case in enumerate(cases, 1):
            try:
                actual = run_reference(fn, case)
                expected = case.get('expected', case.get('expected_groups'))
                if results_equal(actual, expected, case, p['id']):
                    passed += 1
                    print(f"[PASS] {p['id']} case {i}")
                else:
                    failed += 1
                    print(f"[FAIL] {p['id']} case {i}: expected={expected!r}, actual={actual!r}")
            except Exception as exc:
                failed += 1
                print(f"[ERROR] {p['id']} case {i}: {type(exc).__name__}: {exc}")
    print(f'\nResult: {passed} passed, {failed} failed')
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
