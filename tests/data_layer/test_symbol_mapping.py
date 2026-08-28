import unittest

from data_layer.symbol_map import normalize_logical, resolve_symbol


class _Info(object):
    def __init__(self, name):
        self.name = name


class _FakeMT5(object):
    def __init__(self, names):
        self.names = names
        self.selected = []

    def symbols_get(self):
        return [_Info(name) for name in self.names]

    def symbol_info(self, name):
        if name in self.names:
            return _Info(name)
        return None

    def symbol_select(self, name, flag):
        self.selected.append((name, flag))
        return True


class TestSymbolMapping(unittest.TestCase):
    def test_logical_aliases(self):
        self.assertEqual(normalize_logical("gold"), "GOLD")
        self.assertEqual(normalize_logical("XAUUSD"), "GOLD")
        self.assertEqual(normalize_logical("OIL"), "OIL")
        self.assertEqual(normalize_logical("CrudeOIL"), "OIL")

    def test_discovers_gold_not_hardcoded(self):
        mt5 = _FakeMT5(["EURUSD", "GOLD", "USDJPY"])
        logical, actual = resolve_symbol(mt5, "GOLD")
        self.assertEqual(logical, "GOLD")
        self.assertEqual(actual, "GOLD")

    def test_discovers_xauusd_when_gold_missing(self):
        mt5 = _FakeMT5(["XAUUSD.a", "EURUSD"])
        logical, actual = resolve_symbol(mt5, "GOLD")
        self.assertEqual(logical, "GOLD")
        self.assertEqual(actual, "XAUUSD.a")

    def test_discovers_crudeoil(self):
        mt5 = _FakeMT5(["CrudeOIL", "EURUSD"])
        logical, actual = resolve_symbol(mt5, "OIL")
        self.assertEqual(actual, "CrudeOIL")

    def test_unknown_logical_rejected(self):
        with self.assertRaises(ValueError):
            normalize_logical("BTCUSD")


if __name__ == "__main__":
    unittest.main()
