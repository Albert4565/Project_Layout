import unittest
from main import calculate_fines

class TestFingerMovement(unittest.TestCase):
    def test_no_fine(self):
        self.assertEqual(calculate_fines((1, 2), (1, 2)), 0)

    def test_fine_one(self):
        self.assertEqual(calculate_fines((2, 3), (1, 3)), 1)

    def test_fine_two(self):
        self.assertEqual(calculate_fines((2, 4), (3, 5)), 2)

if __name__ == "__main__":
    unittest.main()