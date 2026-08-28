import os
import unittest

from research_engine.alpha_program.universe.scanner import build_universe
from research_engine.errors import FinalOosAccessDenied
from research_engine.holdout import final_oos_access


class TestAlphaUniverse(unittest.TestCase):
    def test_scan_has_required_fields(self):
        payload = build_universe()
        self.assertGreaterEqual(payload["n"], 20)
        self.assertFalse(payload["FINAL_OOS_TOUCHED"])
        for row in payload["records"]:
            for key in ("id", "type", "mechanism", "asset", "timeframe", "status", "evidence", "next_action"):
                self.assertIn(key, row)
            self.assertIn(row["status"], ("DONE", "FAILED", "UNKNOWN", "BLOCKED"))

    def test_scan_sees_frozen_families(self):
        payload = build_universe()
        ids = set(r["id"] for r in payload["records"])
        self.assertIn("CROSS_ASSET_ALPHA_V0.8", ids)
        self.assertIn("PROFIT_DISCOVERY_V0.6", ids)
        self.assertIn("REGIME_TRANSITION_V0.9", ids)
        self.assertIn("RP-IV", ids)

    def test_datasets_have_hashes(self):
        payload = build_universe()
        self.assertIn("tm-market-GOLD-D1-20260825-000001", payload["dataset_hashes"])
        self.assertEqual(
            payload["dataset_hashes"]["tm-market-GOLD-D1-20260825-000001"],
            "49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899",
        )

    def test_no_oos_during_scan(self):
        build_universe()
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()

    def test_deterministic_hash(self):
        a = build_universe()
        b = build_universe()
        self.assertEqual(a["content_hash"], b["content_hash"])

    def test_root_exists(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.assertTrue(os.path.isdir(os.path.join(root, "docs")))
        self.assertTrue(os.path.isdir(os.path.join(root, "research_engine")))
