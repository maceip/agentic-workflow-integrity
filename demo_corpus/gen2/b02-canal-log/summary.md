b02-canal-log is a volunteer project where score must add ten to the input.
score in src/core.py returned value + 1 instead of value + 10, causing tests/test_core.py to fail with 6 != 15 for score(5).
Fix applied: changed src/core.py line 2 from `return value + 1` to `return value + 10`.
Reran python3 tests/test_core.py: 1 test passed (OK).
