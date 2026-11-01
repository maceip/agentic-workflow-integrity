Project purpose: b08-pond-census is a volunteer project exposing a score function in src/core.py.
The score function must return the input value plus ten.
Bug found: score returned value + 1, so score(5) produced 6 instead of the expected 15.
Fix applied: changed the return statement in src/core.py from value + 1 to value + 10.
Verification: ran python3 tests/test_core.py and the test suite passed.
