import unittest

from data_layer.errors import DatasetImmutableError
from data_layer.storage import (
    ensure_layout,
    freeze_dataset,
    next_dataset_id,
)
from tests.data_layer.helpers import make_series, temp_root


class TestImmutable(unittest.TestCase):
    def test_second_save_cannot_overwrite(self):
        root = temp_root()
        ensure_layout(root)
        bars = make_series(3)
        dataset_id = "tm-market-GOLD-M15-20260825-000001"
        freeze_dataset(root, dataset_id, bars, {"dataset_id": dataset_id, "sha256": None}, {})
        with self.assertRaises(DatasetImmutableError):
            freeze_dataset(root, dataset_id, bars, {"dataset_id": dataset_id, "sha256": None}, {})

    def test_second_id_is_new(self):
        root = temp_root()
        ensure_layout(root)
        first = next_dataset_id(root, "GOLD", "M15", "20260825")
        freeze_dataset(root, first, make_series(2), {"dataset_id": first, "sha256": None}, {})
        second = next_dataset_id(root, "GOLD", "M15", "20260825")
        self.assertNotEqual(first, second)
        self.assertTrue(second.endswith("000002"))


if __name__ == "__main__":
    unittest.main()
