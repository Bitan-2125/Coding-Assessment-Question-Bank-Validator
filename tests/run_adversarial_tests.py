"""
Adversarial and property-based tests for DSA reference solutions.
Uses Hypothesis for randomized/generative testing plus explicit edge-case suites.

Run from project root:
    python tests/run_adversarial_tests.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import reference_solutions as sol

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ── test registry ────────────────────────────────────────────────────────────

_failures: list[str] = []
_passed = 0


def record(label: str, ok: bool, detail: str = ""):
    global _passed
    if ok:
        _passed += 1
    else:
        _failures.append(f"[FAIL]  {label}: {detail}")


# ── DSA001: two_sum ──────────────────────────────────────────────────────────

def test_two_sum_edge():
    # No valid pair
    record("two_sum empty", sol.two_sum([], 0) == [-1, -1])
    # Single element
    record("two_sum single", sol.two_sum([5], 5) == [-1, -1])
    # Pair at extremes
    record("two_sum extremes", sol.two_sum([1, 2, 3, 4], 5) in ([0, 3], [1, 2]))
    # Negative targets
    record("two_sum negatives", sol.two_sum([-3, 1, 4], -2) == [0, 1])
    # Duplicate values
    record("two_sum duplicates", sol.two_sum([3, 3], 6) == [0, 1])


@given(st.lists(st.integers(-10**6, 10**6), min_size=2, max_size=200))
@settings(max_examples=300)
def test_two_sum_property(nums):
    """If a pair exists, the returned indices must actually sum to target."""
    target = nums[0] + nums[-1]  # always a valid pair
    i, j = sol.two_sum(nums, target)
    if i == -1:
        # brute-force verify no pair exists
        found = any(
            nums[a] + nums[b] == target
            for a in range(len(nums))
            for b in range(a + 1, len(nums))
        )
        record("two_sum property (no pair)", not found,
               f"claimed no pair but brute force found one in {nums[:5]}")
    else:
        record("two_sum property", i != j and nums[i] + nums[j] == target,
               f"indices {i},{j} don't sum to {target} in {nums[:5]}")


# ── DSA002: is_anagram ───────────────────────────────────────────────────────

def test_anagram_edge():
    record("anagram empty", sol.is_anagram("", "") is True)
    record("anagram single match", sol.is_anagram("a", "a") is True)
    record("anagram single mismatch", sol.is_anagram("a", "b") is False)
    record("anagram length diff", sol.is_anagram("ab", "a") is False)
    record("anagram case sensitive", sol.is_anagram("A", "a") is False)


@given(st.text(alphabet="abcdefghij", min_size=0, max_size=1000))
@settings(max_examples=300)
def test_anagram_sorted_invariant(s):
    """Sorting both strings should always produce a true anagram."""
    t = "".join(sorted(s))
    record("anagram sorted invariant", sol.is_anagram(s, t) is True,
           f"sorted string not recognised as anagram for {s[:20]!r}")


# ── DSA005: binary_search ────────────────────────────────────────────────────

def test_binary_search_edge():
    record("bsearch empty", sol.binary_search([], 1) == -1)
    record("bsearch single hit", sol.binary_search([7], 7) == 0)
    record("bsearch single miss", sol.binary_search([7], 0) == -1)
    record("bsearch first element", sol.binary_search([1, 2, 3, 4, 5], 1) == 0)
    record("bsearch last element", sol.binary_search([1, 2, 3, 4, 5], 5) == 4)
    record("bsearch all same hit", sol.binary_search([4, 4, 4], 4) in [0, 1, 2])
    record("bsearch all same miss", sol.binary_search([4, 4, 4], 5) == -1)


@given(st.lists(st.integers(-10**9, 10**9), min_size=0, max_size=500).map(sorted))
@settings(max_examples=300)
def test_binary_search_property(nums):
    unique = list(dict.fromkeys(nums))
    if unique:
        target = unique[len(unique) // 2]
        idx = sol.binary_search(nums, target)
        record("bsearch hit", idx != -1 and nums[idx] == target,
               f"target {target} not found correctly in {nums[:5]}")
    # miss case
    miss = max(nums, default=0) + 1
    record("bsearch miss", sol.binary_search(nums, miss) == -1,
           f"should have returned -1 for {miss} in {nums[:5]}")


# ── DSA007: max_subarray ─────────────────────────────────────────────────────

def test_max_subarray_edge():
    record("maxsub single", sol.max_subarray([42]) == 42)
    record("maxsub all neg", sol.max_subarray([-5, -2, -9]) == -2)
    record("maxsub all pos", sol.max_subarray([1, 2, 3]) == 6)
    record("maxsub large neg", sol.max_subarray([-10**9]) == -10**9)


@given(st.lists(st.integers(-10**6, 10**6), min_size=1, max_size=500))
@settings(max_examples=300)
def test_max_subarray_property(nums):
    result = sol.max_subarray(nums)
    # brute force O(n^2)
    expected = max(
        sum(nums[i:j])
        for i in range(len(nums))
        for j in range(i + 1, len(nums) + 1)
    )
    record("maxsub property", result == expected,
           f"got {result}, expected {expected} for {nums[:5]}")


# ── DSA008: max_stock_profit ─────────────────────────────────────────────────

def test_stock_edge():
    record("stock single", sol.max_stock_profit([5]) == 0)
    record("stock all same", sol.max_stock_profit([3, 3, 3]) == 0)
    record("stock strictly down", sol.max_stock_profit([9, 8, 7, 6]) == 0)
    record("stock big jump", sol.max_stock_profit([1, 1000000]) == 999999)


@given(st.lists(st.integers(0, 10**6), min_size=1, max_size=500))
@settings(max_examples=300)
def test_stock_property(prices):
    result = sol.max_stock_profit(prices)
    expected = max(
        (prices[j] - prices[i] for i in range(len(prices)) for j in range(i + 1, len(prices))),
        default=0
    )
    # profit can't be negative — matches the spec "return 0 if no profit possible"
    expected = max(expected, 0)
    record("stock property", result == expected,
           f"got {result}, expected {expected} for {prices[:5]}")


# ── DSA010: is_balanced ──────────────────────────────────────────────────────

def test_balanced_edge():
    record("balanced empty", sol.is_balanced("") is True)
    record("balanced single open", sol.is_balanced("(") is False)
    record("balanced single close", sol.is_balanced(")") is False)
    record("balanced mismatched", sol.is_balanced("([)]") is False)
    record("balanced nested", sol.is_balanced("{[({})]}") is True)
    record("balanced long mismatch", sol.is_balanced("(((((((" + "))" * 3) is False)


@given(st.lists(st.sampled_from(["()", "[]", "{}"]), min_size=0, max_size=50))
@settings(max_examples=300)
def test_balanced_property_valid(pairs):
    """Any sequence of complete pair strings is balanced."""
    s = "".join(pairs)
    record("balanced valid pairs", sol.is_balanced(s) is True,
           f"should be True for {s!r}")


# ── DSA014: missing_number ───────────────────────────────────────────────────

def test_missing_edge():
    record("missing empty", sol.missing_number([]) == 0)
    record("missing [0]", sol.missing_number([0]) == 1)
    record("missing [1]", sol.missing_number([1]) == 0)
    record("missing large", sol.missing_number(list(range(100000))) == 100000)


@given(st.integers(1, 1000))
@settings(max_examples=200)
def test_missing_property(n):
    import random
    nums = list(range(n + 1))
    missing = random.randint(0, n)
    nums.pop(missing)
    record("missing property", sol.missing_number(nums) == missing,
           f"expected {missing}, got {sol.missing_number(nums)}")


# ── DSA019: coin_change ──────────────────────────────────────────────────────

def test_coin_change_edge():
    record("coins amount=0", sol.coin_change([1, 5], 0) == 0)
    record("coins impossible", sol.coin_change([2], 3) == -1)
    record("coins single coin exact", sol.coin_change([7], 7) == 1)
    record("coins greedy fails", sol.coin_change([1, 3, 4], 6) == 2)


# ── DSA020: merge_intervals ──────────────────────────────────────────────────

def test_merge_intervals_edge():
    record("merge empty", sol.merge_intervals([]) == [])
    record("merge single", sol.merge_intervals([[1, 2]]) == [[1, 2]])
    record("merge all same", sol.merge_intervals([[1, 3], [1, 3]]) == [[1, 3]])
    record("merge touching", sol.merge_intervals([[1, 2], [2, 3]]) == [[1, 3]])
    record("merge no overlap", sol.merge_intervals([[1, 2], [5, 6]]) == [[1, 2], [5, 6]])


@given(st.lists(
    st.integers(0, 1000).flatmap(lambda a: st.integers(a, a + 100).map(lambda b: [a, b])),
    min_size=0, max_size=100,
))
@settings(max_examples=300)
def test_merge_intervals_property(intervals):
    merged = sol.merge_intervals(intervals)
    if not merged:
        return
    # No two merged intervals should overlap
    for i in range(len(merged) - 1):
        ok = merged[i][1] < merged[i + 1][0]
        record("merge no overlap after merge", ok,
               f"overlap between {merged[i]} and {merged[i+1]}")
    # Total coverage must be preserved (sum of lengths)
    orig_cover = set()
    for a, b in intervals:
        orig_cover.update(range(a, b + 1))
    merged_cover = set()
    for a, b in merged:
        merged_cover.update(range(a, b + 1))
    record("merge coverage preserved", orig_cover == merged_cover,
           f"coverage mismatch for {intervals[:3]}")


# ── runner ───────────────────────────────────────────────────────────────────

def run_all():
    test_two_sum_edge()
    test_two_sum_property()

    test_anagram_edge()
    test_anagram_sorted_invariant()

    test_binary_search_edge()
    test_binary_search_property()

    test_max_subarray_edge()
    test_max_subarray_property()

    test_stock_edge()
    test_stock_property()

    test_balanced_edge()
    test_balanced_property_valid()

    test_missing_edge()
    test_missing_property()

    test_coin_change_edge()

    test_merge_intervals_edge()
    test_merge_intervals_property()

    for msg in _failures:
        print(msg)
    print(f"\nResult: {_passed} passed, {len(_failures)} failed")
    return len(_failures)


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
