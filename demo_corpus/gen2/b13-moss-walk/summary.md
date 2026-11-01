Project purpose: b13-moss-walk is a volunteer project whose score function must double the input value.
Bug found: score(value) in src/core.py returned value + 1, so score(21) produced 22 instead of the expected 42.
Test evidence: python3 tests/test_core.py failed with AssertionError: 22 != 42 in TestScore.test_score.
Fix applied: changed the return statement in src/core.py from value + 1 to value * 2.
Verification: reran python3 tests/test_core.py and the single test passed (OK, exit 0).
