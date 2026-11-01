import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from core import score

class TestScore(unittest.TestCase):
    def test_score(self):
        self.assertEqual(score(4), 16)

if __name__ == '__main__':
    unittest.main()
