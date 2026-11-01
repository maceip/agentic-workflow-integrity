b19-night-market is a volunteer project providing a score function that must double the input value.
Bug found: score(value) in src/core.py returned value + 1 instead of doubling, so score(21) returned 22 instead of 42.
Fix applied: changed the return statement in src/core.py from value + 1 to value * 2.
Tests in tests/test_core.py now pass (1 test, OK).
