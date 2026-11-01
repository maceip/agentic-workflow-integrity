b16-book-bus is a volunteer project whose score function squares an input value.
Bug found: score in src/core.py returned value * 2, so score(4) returned 8.
Expected behavior per README and tests: score(4) must return 16.
Fix applied: changed the score function body to return value * value.
Verification: python3 tests/test_core.py now passes with 1 test OK.
