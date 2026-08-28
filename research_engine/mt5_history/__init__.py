"""MT5 maximum-history extraction. Read-only. New IDs only."""

MISSION_ID = "MT5_MAX_MISSION_V4"
START_COMMIT = "f830a20784dcb37619b6090b8be06c8dd8977cfe"
FROZEN_TOKEN = "20260825-000001"
PROBE_STEPS = (2000, 5000, 10000, 20000, 50000, 100000, 250000)
TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1")
TF_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
    "MN1": 43200,
}
TF_ATTR = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
    "W1": "TIMEFRAME_W1",
    "MN1": "TIMEFRAME_MN1",
}
ACQUIRE_RULES = {
    "D1": 10.0,
    "H1": 5.0,
    "M15": 2.0,
    "H4": 5.0,
}
