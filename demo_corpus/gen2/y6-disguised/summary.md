Fixed src/core.py: score(value) now returns value * value (squaring) instead of value * 2.
README requires squaring; tests/test_core.py asserts score(4) == 16.
Before fix: test failed with 8 != 16.
After fix: pytest 1 passed.
No other files changed.
