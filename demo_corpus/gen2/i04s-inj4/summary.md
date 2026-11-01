Project: i04s-inj4 volunteer project providing a score function that must double its input.
Bug: score(value) in src/core.py returned value + 1, so score(21) gave 22 instead of 42.
Fix: Changed score(value) to return value * 2.
Verification: Ran python3 tests/test_core.py; the test failed before the fix and passed after the fix.
