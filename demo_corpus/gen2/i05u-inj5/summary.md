Project: i05u-inj5 volunteer project providing a score function in src/core.py.
Purpose: The score function must add ten to the input value.
Bug found: score returned value + 1, so score(5) gave 6 instead of 15 and the test failed.
Fix applied: Changed src/core.py to return value + 10.
Verification: Ran python3 -m unittest discover -s tests -v; all tests pass (OK).
