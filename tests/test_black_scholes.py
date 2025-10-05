import math
import unittest
import sys
import os

# Ensure src is on path
tests_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(tests_dir, ".."))
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from bs_pricer.black_scholes import black_scholes_price, greeks


class TestBlackScholes(unittest.TestCase):
    def test_call_price_no_dividend(self):
        # Known value: S=100, K=100, r=5%, sigma=20%, T=1
        price = black_scholes_price("call", 100, 100, 0.05, 0.2, 1.0, 0.0)
        self.assertAlmostEqual(price, 10.4506, places=3)

    def test_put_price_no_dividend(self):
        price = black_scholes_price("put", 100, 100, 0.05, 0.2, 1.0, 0.0)
        self.assertAlmostEqual(price, 5.5735, places=3)

    def test_greeks_shapes(self):
        g = greeks("call", 100, 100, 0.05, 0.2, 1.0, 0.0)
        for k in ["delta", "gamma", "theta", "vega", "rho"]:
            self.assertIn(k, g)
            self.assertTrue(isinstance(g[k], float))


if __name__ == "__main__":
    unittest.main()
