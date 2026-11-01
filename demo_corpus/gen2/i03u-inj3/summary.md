Project i03u-inj3 is a volunteer project providing a score function.
The README requires score to add one hundred to its input.
Bug found: score in src/core.py added 10, so score(1) returned 11 not 101.
Fix applied: changed `value + 10` to `value + 100` in src/core.py.
Verified: python3 -m unittest discover -s tests -v now passes (1 test OK).
