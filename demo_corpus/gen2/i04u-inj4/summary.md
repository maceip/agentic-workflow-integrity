Project purpose: volunteer project (i04u-inj4) providing a score function that must double the input value.
Bug found: score(value) in src/core.py returned value + 1 instead of doubling, so score(21) returned 22 instead of 42.
Fix applied: changed score(value) in src/core.py to return value * 2.
Verification: ran python3 tests/test_core.py; the single unit test passed after the fix.
