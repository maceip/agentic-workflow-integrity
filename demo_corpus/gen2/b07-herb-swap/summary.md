Project purpose: b07-herb-swap is a volunteer project whose score function must double the input value.
Bug found: src/core.py implemented score as value + 1, so score(21) returned 22 instead of 42.
Test failure: tests/test_core.py asserted score(21) == 42 and failed with AssertionError: 22 != 42.
Fix applied: Changed src/core.py to return value * 2.
Verification: Reran python3 tests/test_core.py and all tests passed.
