import os
import unittest

from data_layer.errors import DataLayerReadOnlyError
from data_layer.readonly_mt5 import ReadOnlyMT5


class _FakeMT5(object):
    TIMEFRAME_M15 = 15

    def initialize(self):
        return True

    def last_error(self):
        return (1, "ok")

    def copy_rates_range(self, *args):
        return []

    def order_send(self, request):
        return {"retcode": 10009}

    def positions_get(self):
        return []


class TestReadOnly(unittest.TestCase):
    def test_order_send_raises(self):
        wrapped = ReadOnlyMT5(_FakeMT5())
        with self.assertRaises(DataLayerReadOnlyError) as ctx:
            wrapped.order_send({"action": 1})
        self.assertEqual(str(ctx.exception), "DATA_LAYER_READ_ONLY")

    def test_positions_get_raises(self):
        wrapped = ReadOnlyMT5(_FakeMT5())
        with self.assertRaises(DataLayerReadOnlyError):
            wrapped.positions_get()

    def test_allowed_calls_pass(self):
        wrapped = ReadOnlyMT5(_FakeMT5())
        self.assertTrue(wrapped.initialize())
        self.assertEqual(wrapped.copy_rates_range("GOLD", 15, None, None), [])
        self.assertIs(wrapped.TIMEFRAME_M15, _FakeMT5.TIMEFRAME_M15)

    def test_source_does_not_call_order_send(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data_layer"))
        offenders = []
        for name in os.listdir(root):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            if "order_send(" in text:
                offenders.append(name)
        self.assertEqual(offenders, [], "Data Layer must not call order_send: %s" % offenders)


if __name__ == "__main__":
    unittest.main()
