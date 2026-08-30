import unittest

from research_engine.v10_model import FINAL_OOS_ACCESS, MAX_INTERACTIONS, NEW_DATA_PURCHASE
from research_engine.v10_model.contract import INTERACTIONS, TARGETS, assert_contract, build_contract
from research_engine.v10_model.features import state_label
from research_engine.v10_model.inventory import FEATURES, build_universe
from research_engine.v10_model.trade import proba_to_side


class TestV10Model(unittest.TestCase):
    def test_contract_locked(self):
        c = build_contract()
        assert_contract(c)
        self.assertEqual(c["FINAL_OOS_ACCESS"], "DENIED")
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertFalse(c["NEW_DATA_PURCHASE"])
        self.assertFalse(NEW_DATA_PURCHASE)
        self.assertEqual(c["target_count"], 2)
        self.assertEqual(c["model_count"], 4)
        self.assertLessEqual(len(c["interactions"]), MAX_INTERACTIONS)
        self.assertEqual(len(TARGETS), 2)

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])

    def test_no_inferred_features(self):
        uni = build_universe()
        kinds = set(f["kind"] for f in uni["features"])
        self.assertNotIn("INFERRED", kinds)
        self.assertEqual(len(FEATURES), uni["n_model_features"])
        for feat in uni["features"]:
            self.assertTrue(feat["allowed_as_model_input"])
            self.assertEqual(feat["simple_rule_status"], "SIMPLE_RULE_KILLED")

    def test_ten_interactions(self):
        self.assertEqual(len(INTERACTIONS), 10)
        ids = [x["id"] for x in INTERACTIONS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_threshold_flat_zone(self):
        self.assertEqual(proba_to_side(0.50, 0.55), 0)
        self.assertEqual(proba_to_side(0.56, 0.55), 1)
        self.assertEqual(proba_to_side(0.40, 0.55), -1)

    def test_five_states(self):
        label = state_label({"ret20": 0.02, "rv20": 0.01, "rv60": 0.02, "spread_pct": 0.0001, "atr14_pct": 0.01})
        self.assertIn(label, ("TREND_LOWVOL", "TREND_HIGHVOL", "RANGE_LOWVOL", "RANGE_HIGHVOL", "WIDE_FRICTION"))


if __name__ == "__main__":
    unittest.main()
