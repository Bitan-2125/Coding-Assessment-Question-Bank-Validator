import copy
import pathlib
import tempfile
import unittest

from validation import BankValidationError, load_bank, results_equal, run_reference, validate_bank


class BankTests(unittest.TestCase):
    def setUp(self):
        self.bank = load_bank()

    def test_valid_bank(self):
        self.assertEqual(len(self.bank['problems']), 30)

    def test_rejects_bad_contracts(self):
        mutations = [
            lambda b: b.update(count=0),
            lambda b: b['problems'].append(copy.deepcopy(b['problems'][0])),
            lambda b: b['problems'][0].update(reference_solution='eval'),
            lambda b: b['problems'][0].update(difficulty='Unknown'),
            lambda b: b['problems'][0]['test_cases'][0].update(args=[]),
            lambda b: b['problems'][0]['test_cases'][0].update(args=['bad', 9]),
            lambda b: b['problems'][0]['test_cases'][0].pop('expected'),
            lambda b: b['problems'][0].update(category='sql'),
            lambda b: b['problems'][0].update(examples={'input':{},'output':0}),
            lambda b: b['problems'][20].update(test_cases=['not executable']),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                bank = copy.deepcopy(self.bank)
                mutate(bank)
                with self.assertRaises(BankValidationError):
                    validate_bank(bank)

    def test_duplicate_keys_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'bank.json'
            for content in ('{"count":1,"count":2}', '{"count":NaN}', '{"count":1e9999}', '{broken'):
                path.write_text(content, encoding='utf-8')
                with self.assertRaises(BankValidationError):
                    load_bank(path)

    def test_results_require_correct_types_and_preserve_duplicates(self):
        self.assertFalse(results_equal(True, 1, {}))
        self.assertFalse(results_equal([1], [True], {}))
        case = {'expected_groups': [['a', 'a'], ['b']]}
        self.assertTrue(results_equal([['b'], ['a', 'a']], None, case))
        self.assertFalse(results_equal([['a'], ['b']], None, case))
        self.assertFalse(results_equal('bad', None, case))

    def test_case_input_is_not_mutated(self):
        case = {'args': [[1, 2]], 'expected': []}
        self.assertEqual(run_reference(lambda values: values.pop(), case), 2)
        self.assertEqual(case['args'], [[1, 2]])

    def test_multiple_valid_answers(self):
        case = {'args': [[1,2,3,4],5], 'expected':[0,3]}
        self.assertTrue(results_equal([1,2], case['expected'], case, 'DSA001'))
        self.assertFalse(results_equal([1,1], case['expected'], case, 'DSA001'))
        case = {'args': [[1,2,2,2,3],2], 'expected':1}
        self.assertTrue(results_equal(3, 1, case, 'DSA005'))
        self.assertFalse(results_equal(True, 1, case, 'DSA005'))
