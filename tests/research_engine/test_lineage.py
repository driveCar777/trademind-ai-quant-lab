import unittest

from research_engine.errors import ResultInvalid
from research_engine.lineage import build_lineage


class TestLineage(unittest.TestCase):
    def test_complete(self):
        row = build_lineage(
            {
                "result_hash": "r" * 64,
                "experiment_id": "tm-exp-1",
                "experiment_hash": "e" * 64,
                "hypothesis_id": "HYP-0001-A",
                "hypothesis_hash": "h" * 64,
                "preregister_hash": "p" * 64,
                "dataset_id": "ds",
                "dataset_hash": "d" * 64,
                "protocol_version": "0.3",
                "feature_version": "f" * 64,
                "code_fingerprint": "c" * 64,
            }
        )
        self.assertTrue(row["lineage_hash"])

    def test_missing(self):
        self.assertRaises(ResultInvalid, build_lineage, {"result_hash": "x"})


if __name__ == "__main__":
    unittest.main()
