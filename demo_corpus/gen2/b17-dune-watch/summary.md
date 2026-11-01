Project: b17-dune-watch, a volunteer project whose score function must negate the input value.
Bug: score(value) returned the value unchanged instead of the value's negation, so score(7) returned 7.
Test result before fix: tests/test_core.py failed with AssertionError 7 != -7.
Fix: changed return value to return -value in src/core.py.
Verification: python3 tests/test_core.py now reports 1 test OK.
