b01-fern-press is a volunteer project whose score function must double the input value.
Bug found: src/core.py implemented score(value) as value + 1, so score(21) returned 22 instead of 42.
The unit test in tests/test_core.py failed with AssertionError: 22 != 42.
Fix applied: changed the return statement in src/core.py to return value * 2.
After the fix, python3 tests/test_core.py passes (1 test, OK).