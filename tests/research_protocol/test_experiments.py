import os
import tempfile
import unittest

from research_protocol.contracts import experiment_id, write_once
from research_protocol.errors import ExperimentImmutableError
from research_protocol.experiments import transition


class TestExperiments(unittest.TestCase):
    def test_state_machine(self):
        self.assertEqual(transition("CREATED", "VALIDATED"), "VALIDATED")
        self.assertEqual(transition("COMPLETED", "FROZEN"), "FROZEN")
        with self.assertRaises(ValueError):
            transition("COMPLETED", "RUNNING")

    def test_write_once(self):
        path = os.path.join(tempfile.mkdtemp(), "exp.json")
        write_once(path, {"experiment_id": experiment_id(seq=1)})
        with self.assertRaises(ExperimentImmutableError):
            write_once(path, {"experiment_id": "other"})


if __name__ == "__main__":
    unittest.main()
