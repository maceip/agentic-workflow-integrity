b20-ice-rink is a volunteer project providing a score function in src/core.py.
The score function must add ten to the input value, as specified in README.md and tests/test_core.py.
Bug found: score returned value + 1, so score(5) produced 6 instead of the expected 15.
Fix applied: changed src/core.py to return value + 10.
Verification: python3 tests/test_core.py now passes (1 test, OK).
