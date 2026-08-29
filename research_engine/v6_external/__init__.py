"""V6 External Exchange Data mission. No READY without bytes. No Ava CFD as futures."""

MISSION_ID = "V6_EXTERNAL_EXCHANGE_V1"
CHECKED_AT = "2026-08-29T08:30:00Z"
VENDOR = "Databento"
DATASET = "GLBX.MDP3"
ENV_DATABENTO = "TRADEMIND_DATABENTO_API_KEY"
CREDIT_USD = 125
STANDARD_USD_PER_MONTH = 199
CREDIT_EXPIRE = "6 months after signup; one set per team"
DATASET_START_UTC = "2010-06-06"
MBO_START_UTC = "2017-05-21"
FORBIDDEN_FIRST_SCHEMAS = (
    "mbo",
    "mbp-10",
    "mbp-1",
    "tbbo",
    "trades",
    "bbo-1s",
    "bbo-1m",
    "ohlcv-1s",
    "ohlcv-1m",
    "ohlcv-1h",
)
FIRST_SCHEMAS = ("ohlcv-1d", "definition", "statistics")
PARENT_SYMBOLS = ("GC.FUT", "CL.FUT")
SECONDARY_PARENTS = ("SI.FUT", "NG.FUT", "6E.FUT", "ZN.FUT")
MIN_PACK = "E"
FAMILY_ID = "TERM_STRUCTURE_V1"
LEVEL = 0
CANDIDATE = 0
