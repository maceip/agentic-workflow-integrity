Project: b09-bakery-queue, a volunteer project whose score function must halve the input value.
Bug found: score in src/core.py returned the input value unchanged, so score(10) returned 10 instead of 5.0.
The test in tests/test_core.py failed with AssertionError: 10 != 5.0.
Fix applied: changed score in src/core.py to return value / 2.
Result: python3 tests/test_core.py now passes (1 test, OK).
