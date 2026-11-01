b03-orchard-map is a volunteer project where the score function must halve the input.
Bug found: score in src/core.py returned the input unchanged, so score(10) gave 10.
The test in tests/test_core.py expected score(10) to equal 5.0 and failed with AssertionError.
Fix applied: changed the return statement to return value / 2.
After the fix, python3 tests/test_core.py passes with OK.
