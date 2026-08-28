import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.errors import HypothesisRejected
from research_engine.hypothesis import make_hypothesis, validate_hypothesis


class TestHypothesisSchema(unittest.TestCase):
    def test_hyp0001_valid(self):
        hyp = hyp_0001_a()
        self.assertTrue(validate_hypothesis(hyp))
        self.assertIn("null_hypothesis", hyp)
        self.assertEqual(hyp["parameters"]["streak_length"], 3)

    def test_money_claim_rejected(self):
        hyp = dict(hyp_0001_a())
        hyp["statement"] = "this strategy may make money"
        hyp.pop("hypothesis_hash", None)
        self.assertRaises(HypothesisRejected, make_hypothesis, hyp)


if __name__ == "__main__":
    unittest.main()
