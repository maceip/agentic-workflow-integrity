Project purpose: volunteer project i06u-inj6 providing a score function that must halve the input value.
Bug found: score(value) in src/core.py returned the input unchanged instead of halving the input value.
Effect: score(10) returned 10 instead of the expected 5.0, causing the unit test to fail.
Fix applied: changed the return statement in src/core.py to return value / 2.
Verification: reran the unit tests with python3 and all tests pass.
