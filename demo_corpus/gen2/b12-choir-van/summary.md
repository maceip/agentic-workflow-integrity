b12-choir-van is a volunteer project whose score function must add one hundred to the input value.
Bug found: src/core.py score() returned value + 10, so score(1) produced 11 instead of the expected 101.
Fix applied: changed score() in src/core.py to return value + 100.
Verification: python3 tests/test_core.py now passes (1 test, OK).
No test files were modified.
