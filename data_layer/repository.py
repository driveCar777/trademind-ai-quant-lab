"""Local dataset API. Not a Master or Xavier route."""

import os

from data_layer.config import load_data_sources
from data_layer.constants import MANIFEST_FILENAME, QUALITY_FILENAME
from data_layer.errors import DataCorruptedError
from data_layer.hashing import verify_file_hash
from data_layer.storage import (
    assert_final_oos_unlocked,
    bars_path,
    dataset_dir,
    ensure_layout,
    load_bars_csv,
    read_json,
)
from data_layer.validation import validate_bars


class DatasetRepository(object):
    def __init__(self, storage_root=None, config=None):
        self.config = config or load_data_sources()
        self.storage_root = storage_root or self.config["storage_root"]
        ensure_layout(self.storage_root)
        assert_final_oos_unlocked(self.storage_root)

    def list_datasets(self):
        manifests_dir = os.path.join(self.storage_root, "manifests")
        items = []
        if not os.path.isdir(manifests_dir):
            return items
        for name in sorted(os.listdir(manifests_dir)):
            if name.endswith(".json"):
                items.append(read_json(os.path.join(manifests_dir, name)))
        return items

    def get_manifest(self, dataset_id):
        path = os.path.join(self.storage_root, "manifests", dataset_id + ".json")
        if not os.path.isfile(path):
            raise KeyError(dataset_id)
        return read_json(path)

    def get_quality(self, dataset_id):
        path = os.path.join(dataset_dir(self.storage_root, dataset_id), QUALITY_FILENAME)
        if not os.path.isfile(path):
            raise KeyError(dataset_id)
        return read_json(path)

    def get_dataset(self, dataset_id):
        return {
            "manifest": self.get_manifest(dataset_id),
            "quality": self.get_quality(dataset_id),
            "bars_path": bars_path(self.storage_root, dataset_id),
        }

    def load_dataset(self, dataset_id):
        self.verify_hash(dataset_id)
        return load_bars_csv(bars_path(self.storage_root, dataset_id))

    def verify_hash(self, dataset_id):
        manifest = self.get_manifest(dataset_id)
        expected = manifest.get("sha256")
        path = bars_path(self.storage_root, dataset_id)
        ok, actual = verify_file_hash(path, expected)
        if not ok:
            raise DataCorruptedError(dataset_id)
        return actual

    def validate_dataset(self, dataset_id):
        manifest = self.get_manifest(dataset_id)
        self.verify_hash(dataset_id)
        bars = load_bars_csv(bars_path(self.storage_root, dataset_id))
        quality = validate_bars(bars, manifest.get("timeframe") or "M15")
        return quality
