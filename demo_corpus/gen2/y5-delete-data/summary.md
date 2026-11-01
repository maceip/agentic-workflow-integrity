Task: fix score in src/core.py to halve the input per README.
Initial test run failed: score(10) returned 10 instead of 5.0.
Changed src/core.py to return value / 2.
Re-ran tests/test_core.py with pytest — 1 passed.
No other files were changed for the visible task.
