"""Stdlib tests only — run from ``app/``: ``python3 -m unittest discover -s tests -p 'test_*.py'``"""

import unittest

from utils.pagination import normalize_pagination


class TestNormalizePagination(unittest.TestCase):
    def test_page_and_limit_minimums(self):
        p, lim, off = normalize_pagination(0, 0)
        self.assertEqual((p, lim, off), (1, 1, 0))

    def test_respects_max_limit(self):
        _, lim, _ = normalize_pagination(1, 500)
        self.assertEqual(lim, 100)

    def test_custom_max_limit(self):
        _, lim, _ = normalize_pagination(1, 50, max_limit=25)
        self.assertEqual(lim, 25)

    def test_offset_second_page(self):
        _, _, off = normalize_pagination(2, 10)
        self.assertEqual(off, 10)


if __name__ == "__main__":
    unittest.main()
