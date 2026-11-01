Project purpose: volunteer project providing a score function that adds ten to the input value.
Bug found: score() in src/core.py returned value + 1, so score(5) gave 6 instead of the expected 15.
Fix applied: changed score() in src/core.py to return value + 10.
Verification: ran python3 tests/test_core.py and all tests passed (OK).
