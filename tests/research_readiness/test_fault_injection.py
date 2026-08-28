import unittest

from research_readiness.fault_injection import run_faults
from tests.research_readiness.helpers import series, write_dataset


class TestFaultInjection(unittest.TestCase):
    def test_all_faults_detected(self):
        src = write_dataset(series(80))
        result = run_faults(src, src + "-faults")
        self.assertTrue(result["FAULT_INJECTION_PASS"])
        self.assertEqual(len(result["cases"]), 8)
        for case in result["cases"]:
            self.assertTrue(case["detected"], case)


if __name__ == "__main__":
    unittest.main()
