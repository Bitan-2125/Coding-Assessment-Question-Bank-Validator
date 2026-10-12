"""Run embedded Python reference-solution test cases. From project root: python tests/run_python_tests.py"""
import json, sys, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
import reference_solutions as sol
bank=json.loads((ROOT/'question_bank.json').read_text(encoding='utf-8'))
funcs={name:getattr(sol,name) for name in dir(sol) if not name.startswith('_') and callable(getattr(sol,name))}
passed=failed=0
for p in bank['problems']:
    if p['category']!='dsa': continue
    fn=funcs.get(p['reference_solution'])
    if fn is None:
        print(f"[SKIP] {p['id']} missing function {p['reference_solution']}"); continue
    for i,case in enumerate(p['test_cases'],1):
        try:
            actual=fn(*case['args'])
            if 'expected_groups' in case:
                norm=lambda groups: sorted((tuple(sorted(g)) for g in groups),key=repr)
                ok=norm(actual)==norm(case['expected_groups'])
            else: ok=actual==case['expected']
            if ok: passed+=1; print(f"[PASS] {p['id']} case {i}")
            else:
                failed+=1; print(f"[FAIL] {p['id']} case {i}: expected={case.get('expected',case.get('expected_groups'))!r}, actual={actual!r}")
        except Exception as e:
            failed+=1; print(f"[ERROR] {p['id']} case {i}: {type(e).__name__}: {e}")
print(f"\nResult: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
