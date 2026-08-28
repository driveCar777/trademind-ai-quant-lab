import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.errors import PreregistrationLocked
from research_engine.preregistration import assert_unchanged, build_preregistration, lock_preregistration


class TestPreregistration(unittest.TestCase):
    def test_lock_and_hash(self):
        pre = build_preregistration(hyp_0001_a())
        locked = lock_preregistration(pre)
        self.assertEqual(locked["status"], "LOCKED")
        self.assertTrue(locked["preregister_hash"])
        self.assertRaises(PreregistrationLocked, lock_preregistration, locked)

    def test_cannot_edit(self):
        locked = lock_preregistration(build_preregistration(hyp_0001_a()))
        dirty = dict(locked)
        dirty["parameters"] = {"streak_length": 99}
        self.assertRaises(PreregistrationLocked, assert_unchanged, locked, dirty)


if __name__ == "__main__":
    unittest.main()
