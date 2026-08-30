import unittest

from research_engine.v11_alloc import FINAL_OOS_ACCESS, NEW_DOWNLOAD, NEW_PURCHASE, NEXT_PRIMARY
from research_engine.v11_alloc.allocation import build_allocation
from research_engine.v11_alloc.coverage import build_coverage
from research_engine.v11_alloc.markets import build_comparison


class TestV11Alloc(unittest.TestCase):
    def test_no_spend(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(NEW_DOWNLOAD)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        alloc = build_allocation()
        self.assertEqual(alloc["spend_this_mission_usd"], 0.0)
        self.assertFalse(alloc["NEW_PURCHASE"])

    def test_coverage_from_disk(self):
        cov = build_coverage()
        self.assertGreaterEqual(cov["n_families"], 36)
        self.assertIn("ML", cov["by_class"])
        self.assertEqual(cov["exhaustion"], "MT5_ALPHA_MARGINAL_VALUE_LOW")
        self.assertEqual(len(cov["qualified_execution_universe"]), 4)

    def test_single_next(self):
        alloc = build_allocation()
        self.assertEqual(NEXT_PRIMARY, "CHINA_A_SHARE_RESEARCH_UNIVERSE")
        self.assertEqual(alloc["NEXT_PRIMARY_RESEARCH_PATH"], NEXT_PRIMARY)
        self.assertEqual(alloc["top1"], "D_CHINA_A_SHARE")
        self.assertNotEqual(alloc["top1"], alloc["top2"])

    def test_ashare_sources_free_first(self):
        m = build_comparison()
        ids = [s["source_id"] for s in m["sources"]]
        self.assertIn("BAOSTOCK", ids)
        paid = [s for s in m["sources"] if s.get("buy") is True]
        self.assertEqual(paid, [])
        self.assertFalse(m["a_share"]["on_disk_research_bars"])


if __name__ == "__main__":
    unittest.main()
