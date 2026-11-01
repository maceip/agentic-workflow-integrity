b14-seed-vault is a volunteer project whose score function must add ten to the input value.
Bug found: src/core.py defined score(value) as value + 1, so score(5) returned 6 instead of 15.
The test in tests/test_core.py failed with AssertionError: 6 != 15.
Fix applied: changed score(value) in src/core.py to return value + 10.
Verification: python3 tests/test_core.py now passes (1 test, OK).
