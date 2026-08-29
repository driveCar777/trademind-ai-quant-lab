"""V5 live MT5 universe. Read-only. Does not overwrite 20260825."""

MISSION_ID = "MARKET_UNIVERSE_V5"
START_POINTER = "d29d3b7388b7d09f4951f8901d7745371be30ab6"
FROZEN_TOKEN = "20260825-000001"
CLASSES = ("FX", "METAL", "ENERGY", "INDEX", "CRYPTO", "RATE", "OTHER")
PROBE_STEPS = (2000, 5000, 10000, 20000, 50000, 80000, 100000)
TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1")
HISTORY_TARGETS = {
    "D1": 10.0,
    "H1": 5.0,
    "H4": 5.0,
    "M15": 2.0,
    "M30": 2.0,
    "W1": 10.0,
    "M1": 0.5,
    "M5": 1.0,
    "MN1": 10.0,
}
CLASS_MAP = {
    "FX": "FX",
    "Metals": "METAL",
    "Energy": "ENERGY",
    "Indices": "INDEX",
    "Crypto": "CRYPTO",
    "Rates": "RATE",
    "Other": "OTHER",
}
