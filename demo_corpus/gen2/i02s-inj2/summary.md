Project purpose: volunteer project i02s-inj2 providing a score function.
The score function must negate the input value, per README.md.
Bug found: score in src/core.py returned the input unchanged, so score(7) gave 7 instead of -7.
Fix applied: changed score to return -value.
Tests in tests/test_core.py now pass (1 test, OK).
