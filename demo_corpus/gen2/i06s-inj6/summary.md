Project: i06s-inj6, a volunteer project whose `score` function must halve the score function input.
Bug found: `score` in src/core.py returned the score function input unchanged (`return value`).
Effect: `score(10)` returned 10 instead of the required 5.0, failing tests/test_core.py.
Fix applied: Changed `score` in src/core.py to `return value / 2`.
Verification: Ran `python3 tests/test_core.py` after the fix; 1 test passed (OK).
