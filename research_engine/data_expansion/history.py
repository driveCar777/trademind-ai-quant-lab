"""Killed-family memory. Do not reopen with z_cut / hold / sign flip."""
from __future__ import print_function

from research_engine.data_expansion.paths import expansion_dir, load_json, repo_root

KILLED_REOPEN_FORBIDDEN = (
    "RSI",
    "MACD",
    "MA",
    "ATR",
    "ADX",
    "Donchian",
    "simple_momentum",
    "simple_reversal",
    "simple_cross_asset",
    "simple_calendar",
    "simple_volume_surprise",
    "simple_iv_zcut",
    "simple_cot_zcut",
    "simple_eia_stocks_zcut",
    "simple_rates_zcut",
    "simple_carry_zcut",
    "simple_supply_zcut",
)


def killed_families():
    return load_json(expansion_dir(), "KILLED_FAMILY_MEMORY_V3.json")


def is_reopen_forbidden(pattern):
    key = str(pattern or "").strip().lower()
    for item in KILLED_REOPEN_FORBIDDEN:
        if item.lower() == key:
            return True
    rows = killed_families().get("records") or []
    for row in rows:
        forbidden = str(row.get("forbidden_reopen_pattern") or "").lower()
        if key and key in forbidden:
            return True
        if key and key == str(row.get("family") or "").lower():
            return True
    return False


def failed_alpha_v2():
    path_dir = os_join_docs()
    return load_json(path_dir, "FAILED_ALPHA_DATABASE_V2.json")


def os_join_docs():
    return __import__("os").path.join(repo_root(), "docs", "research_engine")
