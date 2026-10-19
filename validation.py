"""Question-bank contract. Never import or evaluate code named by bank data."""
import inspect
import json
import pathlib
import re
import math
from copy import deepcopy

from python import reference_solutions as solutions

ROOT = pathlib.Path(__file__).resolve().parent
REFERENCE_NAMES = (
    'two_sum', 'is_anagram', 'first_unique_char', 'move_zeroes', 'binary_search',
    'merge_sorted', 'max_subarray', 'max_stock_profit', 'longest_unique_substring',
    'is_balanced', 'top_k_frequent', 'product_except_self', 'rotate_right',
    'missing_number', 'group_anagrams', 'num_islands', 'shortest_path_unweighted',
    'climb_stairs', 'coin_change', 'merge_intervals',
)
REFERENCES = {name: getattr(solutions, name) for name in REFERENCE_NAMES}


def validate_arguments(name, args):
    """Type and safety domains; human-readable bounds remain editorial metadata."""
    integer = lambda v: type(v) is int
    integers = lambda v: isinstance(v, list) and all(integer(x) for x in v)
    string = lambda v: isinstance(v, str)
    strings = lambda v: isinstance(v, list) and all(string(x) for x in v)
    matrix = lambda v: isinstance(v, list) and all(integers(row) for row in v)
    contracts = {
        'two_sum': (integers, integer), 'is_anagram': (string, string),
        'first_unique_char': (string,), 'move_zeroes': (integers,),
        'binary_search': (integers, integer), 'merge_sorted': (integers, integers),
        'max_subarray': (integers,), 'max_stock_profit': (integers,),
        'longest_unique_substring': (string,), 'is_balanced': (string,),
        'top_k_frequent': (integers, integer), 'product_except_self': (integers,),
        'rotate_right': (integers, integer), 'missing_number': (integers,),
        'group_anagrams': (strings,), 'num_islands': (lambda v: isinstance(v, list) and all(string(row) or strings(row) for row in v),),
        'shortest_path_unweighted': (integer, matrix, integer, integer),
        'climb_stairs': (integer,), 'coin_change': (integers, integer),
        'merge_intervals': (matrix,),
    }
    if not all(check(value) for check, value in zip(contracts[name], args)):
        raise ValueError('argument types do not match the reference contract')
    if name == 'max_subarray' and not args[0]:
        raise ValueError('max_subarray requires a nonempty list')
    if name == 'coin_change' and (args[1] < 0 or any(c <= 0 for c in args[0])):
        raise ValueError('coins must be positive and amount nonnegative')
    if name in ('climb_stairs', 'rotate_right') and args[-1] < 0:
        raise ValueError('step count / rotation must be nonnegative')
    if name == 'num_islands' and args[0]:
        grid = args[0]
        if any(len(row) != len(grid[0]) or any(cell not in ('0', '1') for cell in row) for row in grid):
            raise ValueError('grid must be rectangular and contain only 0/1 strings')
    if name == 'merge_intervals' and any(len(row) != 2 or row[0] > row[1] for row in args[0]):
        raise ValueError('intervals require [start, end] with start <= end')
    if name == 'shortest_path_unweighted':
        n, edges, source, target = args
        if n <= 0 or not 0 <= source < n or not 0 <= target < n or any(len(e) != 2 or any(v < 0 or v >= n for v in e) for e in edges):
            raise ValueError('graph vertices must be in [0,n) and edges must have two vertices')


class BankValidationError(ValueError):
    pass


def results_equal(actual, expected, case, problem_id=None):
    """JSON-strict types; only group-anagram ordering is unspecified."""
    if problem_id == 'DSA001' and expected != [-1, -1]:
        nums, target = case['args']
        return (isinstance(actual, list) and len(actual) == 2 and
                all(type(i) is int and 0 <= i < len(nums) for i in actual) and
                actual[0] != actual[1] and nums[actual[0]] + nums[actual[1]] == target)
    if problem_id == 'DSA005' and expected != -1:
        nums, target = case['args']
        return type(actual) is int and 0 <= actual < len(nums) and nums[actual] == target
    if 'expected_groups' in case:
        if not isinstance(actual, list) or any(
            not isinstance(g, list) or any(not isinstance(s, str) for s in g)
            for g in actual
        ):
            return False
        normalize = lambda groups: sorted(tuple(sorted(g)) for g in groups)
        return normalize(actual) == normalize(case['expected_groups'])
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            results_equal(a, e, {}) for a, e in zip(actual, expected)
        )
    return actual == expected


def validate_bank(bank):
    errors = []
    if not isinstance(bank, dict) or not isinstance(bank.get('problems'), list):
        raise BankValidationError('bank.problems must be a list')
    if not bank['problems']:
        errors.append('bank.problems must not be empty')
    if type(bank.get('count')) is not int or bank['count'] != len(bank['problems']):
        errors.append('bank.count must equal the number of problems')
    seen = set()
    for index, p in enumerate(bank['problems']):
        label = f'problems[{index}]'
        if not isinstance(p, dict):
            errors.append(f'{label}: must be an object')
            continue
        pid = p.get('id')
        if not isinstance(pid, str) or not re.fullmatch(r'(DSA|SQL)\d{3}', pid):
            errors.append(f'{label}: invalid problem id')
        elif pid in seen:
            errors.append(f'{pid}: duplicate problem id')
        else:
            seen.add(pid)
        label = pid if isinstance(pid, str) else label
        for field in ('title', 'topic', 'statement', 'constraints', 'reference_solution',
                      'complexity', 'common_mistakes'):
            if not isinstance(p.get(field), str) or not p[field].strip():
                errors.append(f'{label}.{field}: nonempty string required')
        category = p.get('category')
        if category not in ('dsa', 'sql'):
            errors.append(f'{label}.category: expected dsa or sql')
            continue
        if isinstance(pid, str) and not pid.startswith('DSA' if category == 'dsa' else 'SQL'):
            errors.append(f'{label}: id/category mismatch')
        if p.get('difficulty') not in ('Easy', 'Medium', 'Hard'):
            errors.append(f'{label}.difficulty: invalid difficulty')
        cases = p.get('test_cases')
        if not isinstance(cases, list) or not cases:
            errors.append(f'{label}.test_cases: nonempty list required')
            continue
        if category == 'sql':
            if not isinstance(p.get('schema'), str) or not p['schema'].strip():
                errors.append(f'{label}.schema: nonempty string required')
            for i, case in enumerate(cases, 1):
                if not isinstance(case, dict) or set(case) != {'fixture', 'expected_rows'}:
                    errors.append(f'{label} case {i}: fixture and expected_rows required')
                elif case['fixture'] not in ('sample', 'empty', 'edge') or not isinstance(case['expected_rows'], list) or any(not isinstance(row, list) for row in case['expected_rows']):
                    errors.append(f'{label} case {i}: invalid SQL fixture or rows')
                elif any(type(value) not in (str, int, float, type(None)) for row in case['expected_rows'] for value in row):
                    errors.append(f'{label} case {i}: SQL result cells must be scalar values')
            if {c.get('fixture') for c in cases if isinstance(c, dict) and isinstance(c.get('fixture'), str)} != {'sample', 'empty', 'edge'} or len(cases) != 3:
                errors.append(f'{label}: exactly one sample, empty and edge fixture required')
            continue
        name = p.get('reference_solution')
        fn = REFERENCES.get(name) if isinstance(name, str) else None
        if not callable(fn):
            errors.append(f'{label}: unknown reference function {name!r}')
        for i, case in enumerate(cases, 1):
            prefix = f'{label} case {i}'
            if not isinstance(case, dict) or not isinstance(case.get('args'), list):
                errors.append(f'{prefix}: args must be a list')
                continue
            if ('expected' in case) == ('expected_groups' in case):
                errors.append(f'{prefix}: exactly one expected result required')
            if 'expected_groups' in case and (name != 'group_anagrams' or not isinstance(case['expected_groups'], list) or any(not isinstance(g, list) or any(not isinstance(s, str) for s in g) for g in case['expected_groups'])):
                errors.append(f'{prefix}: expected_groups requires lists of strings for group_anagrams')
            if fn:
                try:
                    inspect.signature(fn).bind(*case['args'])
                    validate_arguments(name, case['args'])
                except (TypeError, ValueError) as exc:
                    errors.append(f'{prefix}: {exc}')
        example = p.get('examples')
        if not isinstance(example, dict) or not isinstance(example.get('input'), dict) or 'output' not in example:
            errors.append(f'{label}.examples: input object and output required')
        elif fn:
            try:
                bound = inspect.signature(fn).bind(**example['input'])
                validate_arguments(name, list(bound.args))
            except (TypeError, ValueError) as exc:
                errors.append(f'{label}.examples: {exc}')
    if errors:
        raise BankValidationError('\n'.join(errors))
    return bank


def load_bank(path=ROOT / 'question_bank.json'):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BankValidationError(f'duplicate JSON key: {key}')
            result[key] = value
        return result

    def reject_constant(value):
        raise BankValidationError(f'non-finite JSON number: {value}')

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            reject_constant(value)
        return number

    try:
        if pathlib.Path(path).stat().st_size > 5_000_000:
            raise BankValidationError('Question bank exceeds 5 MB')
        bank = json.loads(pathlib.Path(path).read_text(encoding='utf-8'),
                          object_pairs_hook=unique_keys, parse_constant=reject_constant,
                          parse_float=finite_float)
    except (OSError, ValueError, RecursionError) as exc:
        raise BankValidationError(f'Cannot load question bank: {exc}') from exc
    return validate_bank(bank)


def run_reference(fn, case):
    return fn(*deepcopy(case['args']))
