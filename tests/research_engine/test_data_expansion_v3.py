import os
import unittest

from research_engine.data_expansion import START_COMMIT
from research_engine.data_expansion.gap import (
    assert_index_iv_not_surface,
    assert_physical_not_all_failed,
    gap_matrix,
)
from research_engine.data_expansion.history import is_reopen_forbidden, killed_families
from research_engine.data_expansion.state import ready_for_research
from research_engine.data_expansion.vendors import cost_ledger, top5
from research_engine.data_sources.blocked import DATABENTO
from research_engine.data_sources.eia import load_observations
from research_engine.data_sources.pipeline import AcquisitionBlocked
from research_engine.data_sources.qualify import BLOCKED, PROBE, READY, qualify
from research_engine.data_sources.schema import SchemaError, validate_futures_row, validate_macro_row


class TestDataExpansionV3(unittest.TestCase):
    def test_start_pointer(self):
        self.assertEqual(START_COMMIT, "98d1297f89e127d6f944ed5836b74bb05922c296")

    def test_gap_distinctions(self):
        assert_index_iv_not_surface()
        assert_physical_not_all_failed()
        payload = gap_matrix()
        self.assertGreaterEqual(len(payload.get("rows") or []), 8)
        row = [r for r in payload["rows"] if r["id"] == "GAP-OPTION-SURFACE"][0]
        self.assertFalse(row["currently_tested"])

    def test_killed_reopen(self):
        self.assertTrue(is_reopen_forbidden("simple_iv_zcut"))
        self.assertTrue(is_reopen_forbidden("SUPPLY_V1"))
        self.assertTrue(any(r["family"] == "SUPPLY_V1" for r in killed_families()["records"]))

    def test_no_fake_ready(self):
        self.assertEqual(ready_for_research(False, True, True), "DATA_BLOCKED")
        self.assertEqual(qualify({"has_bytes": False}), BLOCKED)
        self.assertEqual(qualify({"has_bytes": True, "sample_only": True}), PROBE)
        self.assertEqual(
            qualify(
                {
                    "has_bytes": True,
                    "fail_reasons": [],
                    "lookahead_ok": True,
                    "validation_status": "PASS",
                }
            ),
            READY,
        )

    def test_databento_blocked_without_key(self):
        old = os.environ.pop("TRADEMIND_DATABENTO_API_KEY", None)
        try:
            self.assertEqual(DATABENTO.status(), "CREDENTIAL_REQUIRED")
            with self.assertRaises(AcquisitionBlocked):
                DATABENTO.fetch({})
        finally:
            if old is not None:
                os.environ["TRADEMIND_DATABENTO_API_KEY"] = old

    def test_top5_and_zero_spend(self):
        names = [row["vendor"] for row in top5()]
        self.assertEqual(names[0], "Databento")
        self.assertEqual(cost_ledger()["spent_total"], 0)

    def test_schema_rejects_fake_surprise(self):
        with self.assertRaises(SchemaError):
            validate_macro_row(
                {
                    "timestamp_utc": "2026-01-01T00:00:00Z",
                    "knowledge_timestamp_utc": "2026-01-01T13:30:00Z",
                    "source": "te",
                    "asset": "USD",
                    "field": "surprise",
                    "value": 1,
                    "revision": "final",
                    "event_time": "2026-01-01T13:30:00Z",
                    "publication_time": "2026-01-01T13:30:00Z",
                    "knowledge_time": "2026-01-01T13:30:00Z",
                    "consensus": None,
                }
            )
        validate_futures_row(
            {
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "knowledge_timestamp_utc": "2026-01-01T21:00:00Z",
                "source": "cme",
                "asset": "CL",
                "field": "settlement",
                "value": 70.0,
                "revision": "settle",
                "record_type": "futures_contract",
                "contract": "CLZ26",
                "expiry": "2026-12-01",
                "settlement": 70.0,
                "open_interest": 1,
                "volume": 1,
            }
        )

    def test_eia_prod_observations(self):
        rows = load_observations(
            "tm-alt-EIA-USCRUDE-PROD-W1-20260828-000001",
            "USCRUDE",
            "production",
        )
        self.assertGreater(len(rows), 400)
        self.assertTrue(rows[0]["knowledge_timestamp_utc"].endswith("16:00:00Z"))
