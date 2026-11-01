Project purpose: b24-windmill is a volunteer project where the score function must add one hundred to its input.
Bug found: src/core.py score() returned value + 10, so test_score failed with AssertionError 11 != 101 for score(1).
Fix applied: changed score() in src/core.py to return value + 100.
Tests: python3 tests/test_core.py now passes (Ran 1 test, OK).
