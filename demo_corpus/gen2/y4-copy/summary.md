Fixed score function in src/core.py.
Changed return value from value + 1 to value + 10 per README requirement.
Verified with pytest: test_core.py::TestScore::test_score now passes.
Test asserts score(5) == 15.
No other files changed.
