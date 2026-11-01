Project purpose: b15-rain-gauge is a volunteer project.
Project purpose: The score function in src/core.py must halve the input value.
Bug found: The score function returned the input value unchanged.
Bug found: The test expected score(10) to equal 5.0 but the score function returned 10.
Fix applied: The score function now returns value / 2.
Fix applied: The unit tests in tests/test_core.py now pass.
