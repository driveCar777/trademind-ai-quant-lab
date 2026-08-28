import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.errors import MutationBlocked, PreregistrationLocked
from research_engine.experiment import assert_no_mutation, make_experiment
from research_engine.ledger import empty_rdf, record_change_attempt
from research_engine.preregistration import build_preregistration, lock_preregistration


class TestValidationFreeze(unittest.TestCase):
    def test_parameter_change_is_new_record(self):
        locked = lock_preregistration(build_preregistration(hyp_0001_a()))
        rdf = record_change_attempt(empty_rdf(), "parameter", locked["parameters"], {"streak_length": 4}, "new_hypothesis")
        self.assertEqual(rdf["events"][0]["overwrite_allowed"], False)
        dirty = dict(locked)
        dirty["horizon"] = 99
        self.assertRaises(PreregistrationLocked, lock_preregistration, locked)

    def test_experiment_hash_frozen(self):
        exp = make_experiment(
            {
                "experiment_id": "tm-exp-20260825-000000-002",
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
        after = dict(exp)
        after["seed"] = 1
        self.assertRaises(MutationBlocked, assert_no_mutation, exp, after)


if __name__ == "__main__":
    unittest.main()
