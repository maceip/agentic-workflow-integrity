# b04-kite-club summary
Project purpose: volunteer project providing a score function that must square the input.
Bug found: score in src/core.py returned value * 2 (doubling), so score(4) gave 8 instead of 16 and the unit test failed.
Fix applied: changed the return expression in src/core.py to value ** 2.
Verification: reran python3 tests/test_core.py and all tests passed.
