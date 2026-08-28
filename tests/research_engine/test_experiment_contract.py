import unittest

from research_engine.experiment import experiment_hash, make_experiment


class TestExperimentContract(unittest.TestCase):
    def test_required_and_hash(self):
        exp = make_experiment(
            {
                "experiment_id": "tm-exp-20260825-000000-001",
                "hypothesis_id": "HYP-0001-A",
                "family_id": "FAM-PERSISTENCE-0001",
                "dataset_id": "x",
                "dataset_sha256": "a" * 64,
                "preregister_hash": "b" * 64,
                "protocol_hash": "c" * 64,
                "feature_registry_hash": "d" * 64,
                "execution_hash": "e" * 64,
                "window_hash": "f" * 64,
                "cost_hash": "1" * 64,
                "code_hash": "2" * 64,
                "node_assignment": ["Xavier-01"],
                "created_at": "2026-08-25T00:00:00Z",
                "status": "LOCKED",
                "seed": 20260825,
            }
        )
        self.assertEqual(experiment_hash(exp), exp["experiment_hash"])


if __name__ == "__main__":
    unittest.main()
