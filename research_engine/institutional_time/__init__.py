"""Institutional Time V1.0. Calendar events only. Hash locked. Not weekday."""

from research_engine.opportunity.contract_it import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    IT_ID,
    IT_SEED,
    LOCKED_HASH,
    PARENTS,
)

IT_VERSION = "1.0"
IT_BOOT = 2000
IT_PERM = 2000
IT_BLOCK = 5
IT_FDR_Q = 0.05
IT_FDR_M = 3
OCCUPANCY_FAIL = 0.40
EXPECTED_SHA = {
    "tm-market-GOLD-D1-20260825-000001": "49291ffd05b83fc26fd4765773bad4dcf091735ad288baa5963bbe2e57cee899",
    "tm-market-OIL-D1-20260825-000001": "a22e4213fbbf28e24e892fcce400522885e8208ba9f94bbf41ceed3177808d72",
}
LOGICAL = {
    "tm-market-GOLD-D1-20260825-000001": "GOLD",
    "tm-market-OIL-D1-20260825-000001": "OIL",
}
CONTRACT_EVENTS = (
    "LAST_D1_BAR_OF_CALENDAR_MONTH",
    "FIRST_D1_BAR_OF_CALENDAR_MONTH",
)
