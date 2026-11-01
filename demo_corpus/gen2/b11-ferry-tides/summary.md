Project purpose: b11-ferry-tides is a volunteer project where the score function must negate the input.
Bug found: score(value) in src/core.py returned value unchanged, so score(7) returned 7 instead of -7.
Test failure: tests/test_core.py failed with AssertionError: 7 != -7.
Fix applied: Changed score(value) in src/core.py to return -value.
Verification: Reran python3 tests/test_core.py and the test suite passed (OK).
