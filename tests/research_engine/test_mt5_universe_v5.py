import unittest

from research_engine.mt5_history.classify import classify
from research_engine.mt5_universe import CLASS_MAP, FROZEN_TOKEN, START_POINTER
from research_engine.mt5_universe.qualify import coverage


class TestMt5UniverseV5(unittest.TestCase):
    def test_start_pointer_and_frozen_token(self):
        self.assertEqual(START_POINTER, "d29d3b7388b7d09f4951f8901d7745371be30ab6")
        self.assertEqual(FROZEN_TOKEN, "20260825-000001")

    def test_class_map_from_path(self):
        category, _reason = classify(
            {"name": "FOO", "path": "Forex\\Majors\\EURUSD", "description": "Euro vs US Dollar"}
        )
        self.assertEqual(CLASS_MAP[category], "FX")
        category, _reason = classify(
            {"name": "X", "path": "CFD-Metals\\SILVER", "description": "Silver 10000 oz"}
        )
        self.assertEqual(CLASS_MAP[category], "METAL")

    def test_coverage_labels(self):
        self.assertEqual(coverage("D1", 7.7), "SHORTFALL")
        self.assertEqual(coverage("D1", 33.0), "AVAILABLE")
        self.assertEqual(coverage("M1", 0.0), "NOT_AVAILABLE")
        self.assertEqual(coverage("H1", 5.0), "AVAILABLE")
