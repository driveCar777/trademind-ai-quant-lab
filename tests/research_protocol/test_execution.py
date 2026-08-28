import unittest

from research_protocol.execution import NEXT_BAR_OPEN, signal_and_entry


class TestExecution(unittest.TestCase):
    def test_next_bar_open(self):
        timing = signal_and_entry(10, NEXT_BAR_OPEN)
        self.assertEqual(timing["entry_index"], 11)
        self.assertFalse(timing["current_bar_used_for_execution"])
        self.assertFalse(NEXT_BAR_OPEN["current_bar_allowed"])


if __name__ == "__main__":
    unittest.main()
