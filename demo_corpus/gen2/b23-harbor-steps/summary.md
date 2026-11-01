Project: b23-harbor-steps, a volunteer project where the score function must negate the input.
Bug: score() in src/core.py returned value unchanged, so score(7) gave 7 instead of -7.
Fix: Changed return value to return -value in src/core.py.
Result: python3 tests/test_core.py now passes (1 test OK).
