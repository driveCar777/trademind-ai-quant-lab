import unittest

from data_layer.repository import DatasetRepository
from data_layer.storage import ensure_layout, freeze_dataset
from data_layer.validation import validate_bars
from tests.data_layer.helpers import make_series, temp_root


class TestTwoThousandBars(unittest.TestCase):
    def test_2000_bars_dataset_creates(self):
        root = temp_root()
        ensure_layout(root)
        bars = make_series(2000)
        quality = validate_bars(bars, "M15")
        self.assertIn(quality["validation_status"], ("PASS", "WARN"))
        dataset_id = "tm-market-GOLD-M15-20260825-000001"
        freeze_dataset(
            root,
            dataset_id,
            bars,
            {
                "dataset_id": dataset_id,
                "logical_symbol": "GOLD",
                "mt5_symbol": "GOLD",
                "timeframe": "M15",
                "sha256": None,
                "row_count": 2000,
            },
            quality,
        )
        repo = DatasetRepository(storage_root=root, config={"storage_root": root})
        loaded = repo.load_dataset(dataset_id)
        self.assertEqual(len(loaded), 2000)
        self.assertEqual(repo.get_manifest(dataset_id)["sha256"], repo.verify_hash(dataset_id))


if __name__ == "__main__":
    unittest.main()
