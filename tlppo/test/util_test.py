import sys
sys.path.append("..")
import util

import unittest


class TestUtil(unittest.TestCase):
    def test_distance(self):
        self.assertEqual(util.distance((0,), (10,)), 10)
        self.assertEqual(util.distance((0, 1), (10, 1)), 10)

    def test_negative(self):
        self.assertEqual(util.negative((1, 2, 3)), (-1, -2, -3))

    def test_addition(self):
        self.assertEqual(util.addition((1, 2, 3), (2, 3, 4)), (3, 5, 7))

    def test_addition(self):
        self.assertEqual(util.subtraction((1, 2, 3), (2, 3, 4)), (-1, -1, -1))

    def test_magnitude(self):
        self.assertEqual(util.magnitude((20, 0)), 20)

    def test_normalize(self):
        self.assertEqual(util.normalize((20, 0)), (1, 0))

    def test_direction(self):
        self.assertEqual(util.direction((0, 1), (20, 1)), (1, 0))

    def test_move(self):
        self.assertEqual(util.move((0, 1), (20, 54), util.distance((0, 1), (20, 54))), (20, 54))


if __name__ == '__main__':
    unittest.main()

