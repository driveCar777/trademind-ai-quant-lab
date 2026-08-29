import os
import unittest

from research_engine.data_sources.blocked import DATABENTO
from research_engine.data_sources.databento import DatabentoAdapter
from research_engine.v6_external import FORBIDDEN_FIRST_SCHEMAS
from research_engine.data_sources.pipeline import AcquisitionBlocked
from research_engine.data_sources.qualify import BLOCKED, qualify
from research_engine.v6_external import CREDIT_USD, DATASET, STANDARD_USD_PER_MONTH
from research_engine.v6_external.catalog import catalog, min_pack, recommended_pack, schema_row
from research_engine.v6_external.contract import sealed_contract
from research_engine.v6_external.curve import NotExchangeFuture, feature_panel, reject_broker_symbol
from research_engine.v6_external.knowledge_time import (
    KnowledgeLeak,
    assert_feature_before_target,
    next_session_target_start,
    oi_knowledge_utc,
    same_session_forbidden,
    settlement_knowledge_utc,
)
from research_engine.v6_external.novelty import novelty_decision


class TestV6External(unittest.TestCase):
    def setUp(self):
        self._old_key = os.environ.get("TRADEMIND_DATABENTO_API_KEY")
        os.environ["TRADEMIND_DATABENTO_API_KEY"] = ""

    def tearDown(self):
        if self._old_key is None:
            os.environ.pop("TRADEMIND_DATABENTO_API_KEY", None)
        else:
            os.environ["TRADEMIND_DATABENTO_API_KEY"] = self._old_key

    def test_catalog_glbx_live_facts(self):
        cat = catalog()
        self.assertEqual(cat["dataset"]["dataset_id"], DATASET)
        self.assertEqual(cat["dataset"]["available_from_utc"], "2010-06-06")
        self.assertEqual(set(cat["dataset"]["venues"]), set(["CME", "CBOT", "NYMEX", "COMEX"]))
        self.assertTrue(cat["dataset"]["covers_futures"])
        self.assertTrue(cat["dataset"]["covers_options_on_futures"])
        self.assertEqual(cat["pricing"]["new_user_credits_usd"], CREDIT_USD)
        self.assertEqual(cat["pricing"]["standard_usd_per_month"], STANDARD_USD_PER_MONTH)
        self.assertFalse(cat["pricing"]["historical_requires_monthly_subscription"])
        self.assertEqual(schema_row("ohlcv-1d")["first_date"], "2010-06-06")
        self.assertEqual(schema_row("definition")["first_date"], "2010-06-06")
        self.assertEqual(schema_row("statistics")["first_date"], "2010-06-06")
        self.assertTrue(schema_row("statistics")["oi"])
        self.assertTrue(schema_row("statistics")["settlement"])
        self.assertEqual(schema_row("mbo")["first_date"], "2017-05-21")
        self.assertFalse(schema_row("mbo")["first_pass"])

    def test_min_pack_e(self):
        self.assertEqual(recommended_pack(), "E")
        chosen = [row for row in min_pack()["packs"] if row["id"] == "E"][0]
        self.assertEqual(chosen["schemas"], ["ohlcv-1d", "definition", "statistics"])
        self.assertEqual(chosen["new_mechanism_count"], 3)

    def test_no_key_is_credential_required(self):
        self.assertEqual(DATABENTO.status(), "CREDENTIAL_REQUIRED")
        with self.assertRaises(AcquisitionBlocked):
            DATABENTO.fetch({"schema": "ohlcv-1d"})

    def test_forbidden_first_schemas(self):
        adapter = DatabentoAdapter()
        for schema in ("mbo", "trades", "mbp-10", "bbo-1s"):
            self.assertIn(schema, FORBIDDEN_FIRST_SCHEMAS)
            with self.assertRaises(AcquisitionBlocked):
                adapter.fetch({"schema": schema})

    def test_no_bytes_not_ready(self):
        self.assertEqual(qualify({"has_bytes": False}), BLOCKED)

    def test_novelty_rejects_old_and_accepts_curve(self):
        self.assertEqual(
            novelty_decision("front future price momentum z_cut")["decision"],
            "REJECT",
        )
        self.assertEqual(
            novelty_decision("curve slope and backwardation on exchange settlements")[
                "decision"
            ],
            "ACCEPT",
        )
        self.assertEqual(
            novelty_decision(
                "scarcity priced by curve inversion, not price momentum"
            )["decision"],
            "ACCEPT",
        )
        self.assertEqual(
            novelty_decision("weekly COT commercial crowding")["decision"],
            "REJECT",
        )

    def test_ava_cfd_is_not_a_future(self):
        with self.assertRaises(NotExchangeFuture):
            reject_broker_symbol("GOLD")
        with self.assertRaises(NotExchangeFuture):
            reject_broker_symbol("OIL")

    def test_knowledge_time_no_same_session(self):
        know = settlement_knowledge_utc("2020-01-15")
        self.assertEqual(know, "2020-01-15T21:00:00Z")
        self.assertEqual(oi_knowledge_utc("2020-01-15"), "2020-01-16T21:00:00Z")
        self.assertTrue(same_session_forbidden("2020-01-15", "2020-01-15T00:00:00Z"))
        with self.assertRaises(KnowledgeLeak):
            assert_feature_before_target(know, "2020-01-15T16:00:00Z")
        legal = next_session_target_start(know)
        self.assertEqual(legal, "2020-01-16T00:00:00Z")
        assert_feature_before_target(know, legal)

    def test_curve_features_on_exchange_panel(self):
        rows = [
            {
                "asset": "GC",
                "session_date": "2020-01-15",
                "timestamp_utc": "2020-01-15T00:00:00Z",
                "contract": "GCG20",
                "expiry": "2020-02-26",
                "settlement": 1560.0,
                "open_interest": 100,
                "volume": 10,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-15",
                "timestamp_utc": "2020-01-15T00:00:00Z",
                "contract": "GCJ20",
                "expiry": "2020-04-28",
                "settlement": 1570.0,
                "open_interest": 80,
                "volume": 8,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-16",
                "timestamp_utc": "2020-01-16T00:00:00Z",
                "contract": "GCG20",
                "expiry": "2020-02-26",
                "settlement": 1580.0,
                "open_interest": 90,
                "volume": 12,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-16",
                "timestamp_utc": "2020-01-16T00:00:00Z",
                "contract": "GCJ20",
                "expiry": "2020-04-28",
                "settlement": 1575.0,
                "open_interest": 85,
                "volume": 9,
                "instrument_class": "F",
            },
        ]
        panel = feature_panel(rows)
        self.assertEqual(len(panel), 2)
        self.assertTrue(panel[0]["contango"])
        self.assertFalse(panel[0]["backwardation"])
        self.assertTrue(panel[1]["backwardation"])
        self.assertLess(panel[1]["slope"], panel[0]["slope"])
        self.assertEqual(panel[0]["settlement_knowledge_utc"], "2020-01-15T21:00:00Z")

    def test_contract_is_new_family_and_hashed(self):
        space = sealed_contract()
        self.assertEqual(space["family_id"], "TERM_STRUCTURE_V1")
        self.assertEqual(len(space["hypothesis_ids"]), 3)
        self.assertEqual(space["parents"], "UNASSIGNED_UNTIL_ACQUIRE")
        self.assertEqual(
            space["search_space_hash"],
            "5ce2c888aa5530113d769dda8af3602fc45dd96b2db273a73e764f3bf15bb4d0",
        )
        self.assertEqual(space["FINAL_OOS_ACCESS"], "DENIED")

    def test_normalize_statistics_and_ohlcv(self):
        adapter = DatabentoAdapter()
        raw = (
            "ts_event,ts_ref,symbol,stat_type,price,quantity\n"
            "2020-01-15T21:00:00Z,2020-01-15T00:00:00Z,GCG20,3,1560.2,0\n"
            "2020-01-15T21:00:00Z,2020-01-15T00:00:00Z,GCG20,9,0,120000\n"
        ).encode("utf-8")
        rows = list(adapter.normalize(raw, {"schema": "statistics"}))
        self.assertEqual(len(rows), 2)
        stamped = [adapter.timestamp(row, {"schema": "statistics"}) for row in rows]
        settle = [row for row in stamped if row["field"] == "settlement"][0]
        oi = [row for row in stamped if row["field"] == "open_interest"][0]
        self.assertEqual(settle["knowledge_timestamp_utc"], "2020-01-15T21:00:00Z")
        self.assertEqual(oi["knowledge_timestamp_utc"], "2020-01-16T21:00:00Z")
        report = adapter.validate(stamped, {"schema": "statistics"})
        self.assertEqual(report["validation_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
