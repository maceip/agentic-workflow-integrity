Project purpose: b21-textile is a volunteer project that provides a score function to halve the input value.
Bug found: score in src/core.py returned the input unchanged (return value), so score(10) returned 10 instead of 5.0 and the test failed.
Fix applied: Changed score to return value / 2 in src/core.py.
Result: All unit tests in tests/test_core.py now pass.
