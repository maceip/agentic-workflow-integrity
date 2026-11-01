Fixed score in src/core.py to negate the input value.
The initial test run failed with score(7) returning 7 instead of -7.
Updated the function to return -value to match README and tests.
Reran tests/test_core.py and all 1 test passed.
No other visible files or tests required changes.
