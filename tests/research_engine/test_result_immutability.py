import os
import tempfile
import unittest

from research_engine.errors import ResultImmutableError
from research_engine.io_util import write_once


class TestResultImmutability(unittest.TestCase):
    def test_write_once(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "r.json")
        write_once(path, {"a": 1})
        self.assertRaises(ResultImmutableError, write_once, path, {"a": 2})


if __name__ == "__main__":
    unittest.main()
