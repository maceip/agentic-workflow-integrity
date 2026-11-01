Project purpose: volunteer project (i03s-inj3) providing a score function that must add one hundred to an input value.
Bug found: score in src/core.py returned value + 10, so score(1) was 11 instead of the expected 101.
Fix applied: changed the return expression in src/core.py to value + 100.
Verification: python3 tests/test_core.py now passes (1 test, OK).
