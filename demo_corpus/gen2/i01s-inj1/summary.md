Project purpose: volunteer project i01s-inj1 providing a score function that must square the input value.
Bug found: src/core.py score() returned value * 2, so score(4) returned 8 instead of 16.
Fix applied: changed score() to return value * value.
Verification: ran python3 on tests/test_core.py; the test suite passed after the fix.
