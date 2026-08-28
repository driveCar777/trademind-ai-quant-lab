import unittest

from data_layer.errors import DataCorruptedError
from data_layer.repository import DatasetRepository
from data_layer.storage import bars_path, ensure_layout, freeze_dataset
from tests.data_layer.helpers import make_series, temp_root


class TestHash(unittest.TestCase):
    def _freeze(self, root, dataset_id):
        ensure_layout(root)
        bars = make_series(6)
        manifest = {
            "dataset_id": dataset_id,
            "logical_symbol": "GOLD",
            "mt5_symbol": "GOLD",
            "timeframe": "M15",
            "sha256": None,
        }
        freeze_dataset(root, dataset_id, bars, manifest, {"validation_status": "PASS"})
        return DatasetRepository(storage_root=root, config={"storage_root": root})

    def test_hash_matches_after_write(self):
        root = temp_root()
        dataset_id = "tm-market-GOLD-M15-20260825-000001"
        repo = self._freeze(root, dataset_id)
        digest = repo.verify_hash(dataset_id)
        self.assertEqual(len(digest), 64)

    def test_modified_file_is_corrupted(self):
        root = temp_root()
        dataset_id = "tm-market-GOLD-M15-20260825-000002"
        repo = self._freeze(root, dataset_id)
        path = bars_path(root, dataset_id)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("tamper\n")
        with self.assertRaises(DataCorruptedError):
            repo.verify_hash(dataset_id)


if __name__ == "__main__":
    unittest.main()
