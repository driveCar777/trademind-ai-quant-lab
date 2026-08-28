import unittest

from data_layer.constants import SCHEMA_VERSION
from data_layer.repository import DatasetRepository
from data_layer.storage import ensure_layout, freeze_dataset
from tests.data_layer.helpers import make_series, temp_root


REQUIRED = [
    "dataset_id",
    "logical_symbol",
    "mt5_symbol",
    "timeframe",
    "timeframe_minutes",
    "source",
    "source_type",
    "broker",
    "terminal",
    "terminal_version",
    "python_package_version",
    "retrieved_at_utc",
    "data_start_utc",
    "data_end_utc",
    "row_count",
    "columns",
    "timezone",
    "volume_policy",
    "history_request",
    "sha256",
    "validation_status",
    "schema_version",
    "tick_volume_present",
    "real_volume_present",
    "spread_present",
]


class TestManifest(unittest.TestCase):
    def test_manifest_has_required_fields(self):
        root = temp_root()
        ensure_layout(root)
        bars = make_series(4)
        dataset_id = "tm-market-GOLD-M15-20260825-000001"
        manifest = {
            "dataset_id": dataset_id,
            "parent_dataset_id": None,
            "logical_symbol": "GOLD",
            "mt5_symbol": "GOLD",
            "timeframe": "M15",
            "timeframe_minutes": 15,
            "source": "mt5",
            "source_type": "broker_terminal",
            "broker": None,
            "terminal": None,
            "terminal_version": None,
            "python_package_version": None,
            "retrieved_at_utc": "2026-08-25T00:00:00Z",
            "data_start_utc": bars[0]["timestamp_utc"],
            "data_end_utc": bars[-1]["timestamp_utc"],
            "row_count": len(bars),
            "columns": [
                "timestamp_utc",
                "timestamp_unix",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "real_volume",
                "spread",
            ],
            "timezone": "UTC",
            "volume_policy": "tick_volume_only",
            "history_request": {"method": "copy_rates_range", "requested_count": 4},
            "sha256": None,
            "validation_status": "PASS",
            "schema_version": SCHEMA_VERSION,
            "tick_volume_present": True,
            "real_volume_present": True,
            "spread_present": True,
        }
        quality = {"validation_status": "PASS", "row_count": 4}
        freeze_dataset(root, dataset_id, bars, manifest, quality)
        repo = DatasetRepository(storage_root=root, config={"storage_root": root})
        stored = repo.get_manifest(dataset_id)
        for key in REQUIRED:
            self.assertIn(key, stored)
        self.assertEqual(stored["timezone"], "UTC")
        self.assertTrue(stored["sha256"])
        self.assertIsNone(stored["broker"])


if __name__ == "__main__":
    unittest.main()
