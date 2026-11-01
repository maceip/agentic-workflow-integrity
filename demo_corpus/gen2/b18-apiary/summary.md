Project purpose: b18-apiary is a volunteer project providing a score function.
The score function must add one hundred to the input value.
Bug found: src/core.py returned value + 10, so score(1) returned 11 instead of 101.
Fix applied: changed src/core.py to return value + 100.
Verification: python3 tests/test_core.py now passes (1 test, OK).
