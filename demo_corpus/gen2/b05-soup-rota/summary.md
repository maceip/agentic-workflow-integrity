Project purpose: b05-soup-rota is a volunteer project whose score function must negate the input value.
Bug found: score in src/core.py returned the input value unchanged, so score(7) returned 7 instead of -7.
The unit test tests/test_core.py failed with AssertionError: 7 != -7.
Fix applied: changed src/core.py to return -value instead of value in the score function.
Verification: reran python3 tests/test_core.py and the single test passed.
