b22-owl-box is a volunteer project whose score function must square the input value.
Bug found: score returned value * 2, so score(4) gave 8 instead of the expected 16.
The unit test in tests/test_core.py failed with AssertionError 8 != 16.
Fix applied: changed src/core.py to return value * value.
After the fix, python3 tests/test_core.py passes with OK.
