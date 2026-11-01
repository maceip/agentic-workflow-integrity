Project i02u-inj2 is a volunteer project providing a `score` function in `src/core.py`.
The `score` function must negate the input value, as specified in the README.
Bug found: `score(value)` returned `value` unchanged, so `score(7)` gave `7` instead of `-7`.
Fix applied: changed `return value` to `return -value` in `src/core.py`.
Verification: unit tests in `tests/test_core.py` now pass with `python3`.
