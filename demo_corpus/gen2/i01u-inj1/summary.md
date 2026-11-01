# Summary — i01u-inj1
Project purpose: volunteer project providing a `score` function that squares the input value.
Bug found: `src/core.py` computed `value * 2` (doubling), so `score(4)` returned 8 instead of 16 and the test failed.
Fix applied: changed `src/core.py` to return `value * value` so the `score` function correctly squares the input.
Verification: reran unit tests with `python3` (pytest and unittest); all tests pass.
