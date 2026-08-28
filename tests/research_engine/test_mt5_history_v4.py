import unittest

from research_engine.mt5_history import FROZEN_TOKEN, START_COMMIT
from research_engine.mt5_history.acquire import should_acquire
from research_engine.mt5_history.classify import classify


class TestMt5HistoryV4(unittest.TestCase):
    def test_start_and_frozen_token(self):
        self.assertEqual(START_COMMIT, "f830a20784dcb37619b6090b8be06c8dd8977cfe")
        self.assertEqual(FROZEN_TOKEN, "20260825-000001")

    def test_classify_uses_path_not_name(self):
        category, reason = classify(
            {"name": "FOO", "path": "Forex\\Majors\\EURUSD", "description": "Euro vs US Dollar"}
        )
        self.assertEqual(category, "FX")
        self.assertEqual(reason, "path+description")
        category, _reason = classify(
            {"name": "XAGUSD", "path": "Metals\\Spot\\XAGUSD", "description": "Silver"}
        )
        self.assertEqual(category, "Metals")

    def test_should_not_overwrite_existing_max(self):
        inventory = [
            {
                "logical": "GOLD",
                "timeframe": "D1",
                "dataset_id": "tm-market-GOLD-D1-20260828-000001",
                "years": 7.715,
            }
        ]
        ok, why = should_acquire({"calendar_span": 7.7, "status": "OK"}, "GOLD", "D1", inventory)
        self.assertFalse(ok)
        self.assertIn("already_have", why)

    def test_20260825_is_ignored_as_max(self):
        inventory = [
            {
                "logical": "GOLD",
                "timeframe": "M15",
                "dataset_id": "tm-market-GOLD-M15-20260825-000001",
                "years": 0.05,
            }
        ]
        ok, why = should_acquire({"calendar_span": 2.4, "status": "OK"}, "GOLD", "M15", inventory)
        self.assertTrue(ok)
        self.assertIn("meets", why)

    def test_equity_cfd_not_auto_acquired(self):
        from research_engine.mt5_history.classify import is_equity_cfd

        self.assertTrue(is_equity_cfd({"name": "#AAPL"}))
        ok, why = should_acquire({"calendar_span": 20.0, "status": "OK"}, "AAPL", "D1", [], True)
        self.assertFalse(ok)
        self.assertEqual(why, "equity_cfd_inventory_only")
