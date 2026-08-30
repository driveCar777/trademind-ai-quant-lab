import unittest

from research_engine.profit.cost.model import fill_price
from research_engine.v9_master import CLOSE_FILL, FILL, NEW_DATA_PURCHASE, START_EQUITY
from research_engine.v9_master.classify import MECHANISMS, strategy_families
from research_engine.v9_master.contract import assert_contract, build_contract
from research_engine.v9_master.cost_overlay import CostOverlay
from research_engine.v9_master.metrics_v9 import economic_status, extend_metrics


class TestV9Master(unittest.TestCase):
    def test_contract_locked(self):
        c = build_contract()
        assert_contract(c)
        self.assertEqual(c["execution"]["fill"], FILL)
        self.assertEqual(c["execution"]["close_fill"], CLOSE_FILL)
        self.assertFalse(c["NEW_DATA_PURCHASE"])
        self.assertFalse(NEW_DATA_PURCHASE)
        self.assertEqual(c["FINAL_OOS_ACCESS"], "DENIED")
        self.assertEqual(c["sensitivity_pre_fixed"]["factorial"], False)

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])

    def test_no_close_fill(self):
        bar = {"open": 100.0, "close": 110.0, "spread": 10, "high": 111, "low": 99}
        px = fill_price(bar, 1, False)
        self.assertNotEqual(px, 110.0)
        self.assertGreater(px, 100.0)

    def test_cost_overlay_restores(self):
        import research_engine.profit.cost.model as cm

        before_c = cm.COMMISSION_BP
        before_s = cm.SLIPPAGE_BP
        with CostOverlay(2.0, 20.0):
            self.assertEqual(cm.COMMISSION_BP, before_c * 2.0)
            self.assertEqual(cm.SLIPPAGE_BP, 20.0)
        self.assertEqual(cm.COMMISSION_BP, before_c)
        self.assertEqual(cm.SLIPPAGE_BP, before_s)

    def test_economic_status(self):
        self.assertEqual(
            economic_status({"net_return": 0.1, "trade_count": 10}, {"net_return": 0.05, "trade_count": 5}),
            "POSITIVE_REPRODUCIBLE",
        )
        self.assertEqual(
            economic_status({"net_return": 0.1, "trade_count": 10}, {"net_return": -0.05, "trade_count": 5}),
            "POSITIVE_BUT_WEAK",
        )
        self.assertEqual(
            economic_status({"net_return": -0.1, "trade_count": 10}, {"net_return": -0.05, "trade_count": 5}),
            "LOSS",
        )

    def test_metrics_dd_duration(self):
        curve = [10000, 11000, 9000, 9000, 12000]
        m = extend_metrics(curve, "D1", START_EQUITY, [{"net_pnl": 100}, {"net_pnl": -50}])
        self.assertIn("max_dd_bars", m)
        self.assertIsNotNone(m.get("profit_factor"))
        self.assertLess(m.get("max_drawdown"), 0)

    def test_mechanism_registry(self):
        fams = [m["family"] for m in MECHANISMS]
        self.assertIn("PROFIT_DISCOVERY_V0.6", fams)
        self.assertIn("HYP-0001", fams)
        self.assertTrue(strategy_families())
        hyp = [m for m in MECHANISMS if m["family"] == "HYP-0001"][0]
        self.assertEqual(hyp["replay_kind"], "PREDICTIVE_ONLY")


if __name__ == "__main__":
    unittest.main()
