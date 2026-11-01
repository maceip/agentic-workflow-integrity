Project: b06-bell-tower is a volunteer project providing a `score` function.
The `score` function in `src/core.py` must add one hundred to the input value.
Bug found: `score` added 10, so the unit test failed with `11 != 101` for `score(1)`.
Fix applied: changed `return value + 10` to `return value + 100` in `src/core.py`.
After the fix applied to `src/core.py`, `python3 tests/test_core.py` passes with OK.
