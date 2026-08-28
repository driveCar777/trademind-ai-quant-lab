import unittest

from research_engine.cross_asset.space import canonical_search_space_hash as xa_hash
from research_engine.cross_residual.space import canonical_search_space_hash as xr_hash
from research_engine.errors import FinalOosAccessDenied
from research_engine.forensics.alpha_gap_report import build_report
from research_engine.forensics.calendar_events import count_all, count_events
from research_engine.forensics.failure_analyzer import CODES, analyze
from research_engine.forensics.inventory import TARGETS, acquisition_items, build_capability, inventory_disk
from research_engine.forensics.pipeline import run
from research_engine.forensics.scan import load_rankings, scan_index
from research_engine.forensics.search_space_coverage import coverage_summary, coverage_table
from research_engine.holdout import final_oos_access
from research_engine.information_map.build import build_map
from research_engine.information_map.sources import all_sources
from research_engine.opportunity.catalog import all_opportunities
from research_engine.opportunity.contract_it import (
    LOCKED_HASH,
    build_search_space,
    canonical_search_space_hash,
)
from research_engine.opportunity.score_v2 import item_score, rank_v2
from research_engine.opportunity.select import select_one
from research_engine.regime_transition.space import canonical_search_space_hash as rt_hash


class TestAlphaRecovery(unittest.TestCase):
    def test_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()

    def test_coverage_shape_and_zeros(self):
        table = coverage_table()
        summary = coverage_summary()
        for key in (
            "direction",
            "relative_value",
            "state_transition",
            "risk_premium",
            "event",
            "microstructure",
            "time_institutional",
            "volatility_realized",
        ):
            self.assertIn(key, table)
            self.assertEqual(summary[key], table[key]["covered_pct"])
        self.assertEqual(summary["risk_premium"], 0)
        self.assertEqual(summary["event"], 0)
        self.assertEqual(summary["time_institutional"], 0)
        self.assertGreater(summary["direction"], 50)
        self.assertGreater(summary["state_transition"], 0)
        self.assertGreater(table["microstructure"]["n_covered"], 0)

    def test_every_family_has_ae_codes(self):
        rows = analyze()
        names = [r["family"] for r in rows]
        for wanted in (
            "HYP-0001",
            "FACTOR_DISCOVERY_V0.1",
            "RESEARCH_ENGINE_V0.5",
            "PROFIT_DISCOVERY_V0.6",
            "CROSS_ASSET_ALPHA_V0.8",
            "REGIME_TRANSITION_V0.9",
            "CROSS_RESIDUAL_V0.91",
        ):
            self.assertIn(wanted, names)
        for row in rows:
            self.assertTrue(row.get("codes"))
            for code in row["codes"]:
                self.assertIn(code, CODES)

    def test_gap_report_no_oos(self):
        gap = build_report()
        self.assertFalse(gap["FINAL_OOS_TOUCHED"])
        self.assertIn(gap["dominant_code"], CODES)
        self.assertEqual(len(gap["families"]), 7)

    def test_scan_walks_rankings_datasets_contracts(self):
        index = scan_index()
        self.assertEqual(len(index["rankings"]), 7)
        self.assertGreaterEqual(len(index["datasets"]), 16)
        self.assertGreaterEqual(len(index["contracts"]), 5)
        self.assertGreaterEqual(index["hyp0001_results"]["n_files"], 20)

    def test_rankings_exist(self):
        rows = load_rankings()
        found = {r["family"]: r["exists"] for r in rows}
        self.assertTrue(found["FACTOR_DISCOVERY_V0.1"])
        self.assertTrue(found["REGIME_TRANSITION_V0.9"])
        self.assertTrue(found["CROSS_RESIDUAL_V0.91"])

    def test_inventory_targets_recovery_v1(self):
        self.assertEqual(TARGETS["D1"], 10.0)
        self.assertEqual(TARGETS["H1"], 5.0)
        self.assertEqual(TARGETS["M15"], 2.0)
        rows = inventory_disk()
        d1 = [r for r in rows if r["timeframe"] == "D1"]
        h1 = [r for r in rows if r["timeframe"] == "H1"]
        m15 = [r for r in rows if r["timeframe"] == "M15"]
        self.assertTrue(d1)
        self.assertTrue(all(r["coverage"] == "SHORTFALL" for r in d1))
        self.assertTrue(all(r["coverage"] == "SHORTFALL" for r in h1))
        self.assertTrue(all(r["coverage"] == "SHORTFALL" for r in m15))
        gold = [r for r in d1 if r["asset"] == "GOLD"][0]
        self.assertEqual(
            gold["sha256"],
            "49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899",
        )

    def test_acquisition_h1_possible_when_probe_meets(self):
        disk = inventory_disk()
        probe = {
            "ok": True,
            "status": "PROBED",
            "rows": [
                {"asset": "GOLD", "timeframe": "D1", "span_years": 7.7, "coverage": "SHORTFALL", "status": "PROBE_OK"},
                {"asset": "OIL", "timeframe": "D1", "span_years": 7.7, "coverage": "SHORTFALL", "status": "PROBE_OK"},
                {"asset": "EURUSD", "timeframe": "D1", "span_years": 10.0, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "USDJPY", "timeframe": "D1", "span_years": 10.0, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "GOLD", "timeframe": "H1", "span_years": 5.03, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "EURUSD", "timeframe": "H1", "span_years": 5.03, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "USDJPY", "timeframe": "H1", "span_years": 5.03, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "OIL", "timeframe": "H1", "span_years": 5.03, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "GOLD", "timeframe": "M15", "span_years": 2.04, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "EURUSD", "timeframe": "M15", "span_years": 2.04, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "USDJPY", "timeframe": "M15", "span_years": 2.04, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
                {"asset": "OIL", "timeframe": "M15", "span_years": 2.04, "coverage": "MEETS_TARGET", "status": "PROBE_OK"},
            ],
        }
        acq = acquisition_items(disk, probe)
        ids = [i["id"] for i in acq["items"]]
        self.assertEqual(ids[0], "ACQ-H1-5Y")
        self.assertEqual(acq["items"][0]["status"], "ACQUISITION_POSSIBLE")
        cap = build_capability(disk, probe)
        self.assertEqual(cap["overall"], "PROBE_H1_5Y_M15_2Y_OK_GOLD_OIL_D1_SHORT_OF_10Y")

    def test_information_map_status(self):
        rows = {r["id"]: r for r in all_sources()}
        self.assertEqual(rows["INFO-PRICE"]["status"], "FAILED")
        self.assertEqual(rows["INFO-XASSET-PROXY"]["status"], "FAILED")
        self.assertEqual(rows["INFO-RESIDUAL"]["status"], "FAILED")
        self.assertEqual(rows["INFO-IV"]["status"], "BLOCKED")
        self.assertEqual(rows["INFO-MONTH-END"]["status"], "UNKNOWN")
        self.assertFalse(rows["INFO-MONTH-END"]["previously_tested"])
        self.assertTrue(rows["INFO-USD-PROXY"]["killed_isomorph"])
        payload = build_map()
        self.assertEqual(payload["map_id"], "ALPHA_INFORMATION_MAP_V1")
        self.assertFalse(payload["FINAL_OOS_TOUCHED"])

    def test_no_indicator_farm_in_catalog(self):
        text = " ".join("%s %s" % (r["id"], r["mechanism_text"]) for r in all_opportunities()).lower()
        self.assertNotIn("rsi", text)
        self.assertNotIn("macd", text)
        self.assertNotIn("ma cross", text)

    def test_isomorphs_score_zero(self):
        rows = {r["id"]: r for r in all_opportunities()}
        self.assertEqual(item_score(rows["OPP-USD"]), 0)
        self.assertEqual(item_score(rows["OPP-BASKET"]), 0)
        self.assertEqual(item_score(rows["OPP-IV"]), 0)
        self.assertEqual(item_score(rows["OPP-WEEKDAY"]), 0)
        self.assertGreater(item_score(rows["OPP-IT-ME"]), item_score(rows["OPP-RV-TERM"]))

    def test_select_one_institutional_time(self):
        selection = select_one(all_opportunities())
        self.assertEqual(selection["chosen"], "OPP-IT-ME")
        self.assertIn("OPP-IT-ME", selection["eligible"])
        self.assertNotIn("OPP-USD", selection["eligible"])
        self.assertNotIn("OPP-WEEKDAY", selection["eligible"])
        self.assertNotIn("OPP-IT-LON", selection["eligible"])
        self.assertGreaterEqual(len(selection["top10"]), 8)
        why = (selection.get("why") or "").lower()
        self.assertTrue("no contract" in why or "queued" in why)

    def test_rank_v2_deterministic(self):
        a, live_a = rank_v2(all_opportunities())
        b, live_b = rank_v2(all_opportunities())
        self.assertEqual([r["id"] for r in a], [r["id"] for r in b])
        self.assertEqual([r["id"] for r in live_a], [r["id"] for r in live_b])
        self.assertEqual(live_a[0]["id"], "OPP-IT-ME")

    def test_calendar_counts(self):
        gold_like = ["2020-01-02", "2020-01-31", "2020-02-03", "2020-02-28", "2020-03-02", "2020-03-31"]
        ev = count_events(gold_like)
        self.assertEqual(ev["n_month_end"], 3)
        self.assertEqual(ev["n_month_start"], 3)
        self.assertEqual(ev["n_quarter_end"], 1)
        rows = {r["asset"]: r for r in count_all()}
        self.assertEqual(rows["GOLD"]["n_month_end"], 78)
        self.assertEqual(rows["GOLD"]["n_month_start"], 78)
        self.assertEqual(rows["GOLD"]["n_quarter_end"], 26)
        self.assertGreaterEqual(rows["GOLD"]["research_month_end_est"], 8)
        self.assertGreaterEqual(rows["OIL"]["n_month_end"], 70)
        self.assertEqual(
            rows["GOLD"]["sha256"],
            "49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899",
        )
        self.assertEqual(
            rows["OIL"]["sha256"],
            "a22e4213fbbf28e24e892fcce400522885e8208ba9f94bbf41ceed3177808d72",
        )

    def test_contract_locked_not_run(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457",
        )
        space = build_search_space()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        self.assertFalse(space["executed"])
        self.assertEqual(space["runner"], "NONE")
        self.assertEqual(space["hypothesis_count"], 3)
        self.assertEqual(space["hold_bars"], 5)
        self.assertEqual(space["windows"]["FINAL_OOS_ACCESS"], "DENIED")
        self.assertTrue(space["calendar"]["not_weekday"])
        self.assertEqual(space["calendar"]["widen_after_pnl"], "FORBIDDEN")
        kinds = [h["kind"] for h in space["hypotheses"]]
        self.assertEqual(kinds, ["MONTH_END", "MONTH_END", "MONTH_START"])

    def test_frozen_hashes_untouched(self):
        self.assertEqual(xa_hash(), "787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827")
        self.assertEqual(rt_hash(), "3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea")
        self.assertEqual(xr_hash(), "0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57")

    def test_pipeline_deterministic_no_write(self):
        a, extra_a = run(write=False, probe=False)
        b, extra_b = run(write=False, probe=False)
        self.assertEqual(a["content_hash"], b["content_hash"])
        self.assertFalse(a["FINAL_OOS_TOUCHED"])
        self.assertFalse(a["executed_new_family"])
        self.assertEqual(a["selection"]["chosen"], "OPP-IT-ME")
        self.assertIn("ALPHA_RECOVERY_REPORT.md", extra_a["docs"])
        self.assertIn("DATA_CAPABILITY_REAL.md", extra_a["docs"])
        self.assertIn("NEXT_ALPHA_DECISION.md", extra_a["docs"])
        self.assertIn("INSTITUTIONAL_TIME_V1.0_CONTRACT.md", extra_a["docs"])
        self.assertEqual(extra_b["space"]["search_space_hash"], LOCKED_HASH)
        self.assertFalse(extra_a["written"])
        report = extra_a["docs"]["ALPHA_RECOVERY_REPORT.md"]
        self.assertIn("Information-gap codes (A-E)", report)
        self.assertIn("OPP-IT-ME", report)
        self.assertNotIn("RSI", report)
        self.assertNotIn("MACD", report)
