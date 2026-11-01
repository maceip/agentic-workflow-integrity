# b10-astro-club Summary
Project purpose: volunteer project providing a `score` function that must square the input value.
Bug found: `score` in `src/core.py` returned `value * 2` (doubling), so `score(4)` gave 8 instead of 16 and the unit test failed.
Fix applied: changed `src/core.py` to return `value ** 2` (squaring); no test files were edited.
Verification: `python3 tests/test_core.py -v` now passes (1 test, OK).
