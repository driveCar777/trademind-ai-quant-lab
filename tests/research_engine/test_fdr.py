import unittest

from research_engine.statistics import LCG, benjamini_hochberg


class TestFDR(unittest.TestCase):
    def test_known_cutoff(self):
        p = [0.001, 0.008, 0.039, 0.2, 0.5]
        out = benjamini_hochberg(p, q=0.05)
        self.assertEqual(out["m"], 5)
        self.assertTrue(0 in out["discoveries"])
        self.assertEqual(len(out["adjusted_p"]), 5)
        self.assertLessEqual(out["adjusted_p"][0], out["adjusted_p"][1])

    def test_hundred_nulls_reasonable(self):
        rng = LCG(20260825)
        pvals = []
        i = 0
        while i < 100:
            pvals.append((rng.next_u32() + 1) / 4294967296.0)
            i += 1
        out = benjamini_hochberg(pvals, q=0.05)
        self.assertLessEqual(len(out["discoveries"]), 20)
        self.assertEqual(out["q"], 0.05)


if __name__ == "__main__":
    unittest.main()
