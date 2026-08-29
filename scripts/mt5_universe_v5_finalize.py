#!/usr/bin/env python3
"""Qualify 841 listings. Path-first. CFD is not futures. No MT5 attach."""
from __future__ import print_function

import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.mt5_universe.taxonomy import classify_row
from research_protocol.bars import load_json

force_project_temp(ROOT)

UNI_DIR = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")
INV = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history", "MT5_SYMBOL_INVENTORY_V1.json")
CAP = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history", "MT5_HISTORY_CAPABILITY_V1.json")

V4_READY = {
    "GOLD",
    "SILVER",
    "PLATINUM",
    "PALLADIUM",
    "COPPER",
    "WTI",
    "BRENT",
    "NATGAS",
    "GASOLINE",
    "HEATOIL",
    "EURUSD",
    "USDJPY",
    "GBPUSD",
    "AUDUSD",
    "USDCHF",
    "USDCAD",
    "NZDUSD",
    "EURJPY",
    "EURGBP",
    "GBPJPY",
    "US500",
    "US30",
    "GER40",
    "JP225",
    "DXY",
}

CLONE_NAME = {
    "GOLD_FUTURE": "GOLD",
    "SI_FUTURE": "SILVER",
    "CrudeTEST": "WTI",
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def d1_years(asset):
    history = asset.get("timeframes") or {}
    d1 = history.get("D1") or {}
    span = d1.get("calendar_span")
    if span is None:
        depth = asset.get("history_depth") or {}
        span = depth.get("D1")
    try:
        return float(span or 0)
    except Exception:
        return 0.0


def research_status(tax, years, frozen):
    name = tax["symbol"]
    if name in CLONE_NAME:
        return "CLONE", "broker_future_named_cfd"
    if int(tax.get("expiration") or 0) == 0 and tax["instrument_type"] == "FUTURE":
        return "CLONE", "named_future_but_cfd"
    if tax.get("trade_mode") == 0:
        return "BLOCKED", "trade_mode_disabled"
    if tax["path_root"] == "INTERNAL" and tax.get("trade_mode") != 4:
        return "BLOCKED", "internal_disabled_or_close_only"
    if tax["listing_kind"] in ("HASH_CFD", "UNDERSCORE_CFD") and tax["asset_class"] in ("STOCK", "ETF"):
        return "CONDITIONAL", "equity_or_etf_cfd_not_single_name_alpha"
    if tax["asset_class"] == "OTHER" and tax["path_root"] == "CFD-AGRICULTURAL":
        if years >= 5.0 or frozen:
            return "READY", "new_agricultural_class"
        if years >= 2.0:
            return "CONDITIONAL", "agricultural_short_or_unprobed"
        return "SHORTFALL", "agricultural_no_history_yet"
    if tax["economic_underlying"] in V4_READY or frozen:
        return "READY", "already_qualified_v4_or_alias"
    if years >= 5.0 and tax["asset_class"] in ("FX", "METAL", "ENERGY", "INDEX", "BOND"):
        return "READY", "d1_ge_5y"
    if years >= 2.0:
        return "CONDITIONAL", "d1_2_to_5y"
    if years > 0:
        return "SHORTFALL", "d1_below_2y"
    return "SHORTFALL", "stage_a_metadata_only"


def main():
    live = load_json(os.path.join(UNI_DIR, "MT5_UNIVERSE_V5.json"))
    inv = load_json(INV)
    cap = load_json(CAP)
    spec_by_name = {}
    for spec in inv.get("symbols") or []:
        spec_by_name[spec.get("name")] = spec
    frozen_logical = set()
    for row in cap.get("rows") or []:
        if row.get("timeframe") == "D1" and row.get("logical"):
            frozen_logical.add(str(row["logical"]).upper())
    assets = []
    groups = defaultdict(list)
    status_counts = Counter()
    class_counts = Counter()
    type_counts = Counter()
    clones = []
    disabled = []
    shortfall = []
    qualified = []
    usable = []
    history_rows = []
    for raw in live.get("assets") or []:
        name = raw.get("symbol") or raw.get("asset")
        spec = dict(spec_by_name.get(name) or {})
        if raw.get("meta"):
            for key, value in raw["meta"].items():
                if value is not None and key not in spec:
                    spec[key] = value
        spec["name"] = name
        tax = classify_row(spec)
        years = d1_years(raw)
        frozen = tax["economic_underlying"] in V4_READY or tax["economic_underlying"] in frozen_logical
        status, why = research_status(tax, years, frozen)
        if name in CLONE_NAME:
            tax["economic_underlying"] = CLONE_NAME[name]
            status, why = "CLONE", "same_underlying_as_%s" % CLONE_NAME[name]
        row = dict(raw)
        row.update(tax)
        row["d1_years"] = years
        row["research_status"] = status
        row["status_reason"] = why
        row["new_information"] = bool(
            tax["path_root"] == "CFD-AGRICULTURAL"
            or (tax["asset_class"] in ("STOCK", "ETF") and status == "CONDITIONAL")
            or (tax["asset_class"] == "BOND")
            or name in ("ALUMINIUM_SPOT", "NICKEL_SPOT", "US_2000")
        )
        assets.append(row)
        groups[tax["economic_underlying"]].append(name)
        status_counts[status] += 1
        class_counts[tax["asset_class"]] += 1
        type_counts[tax["instrument_type"]] += 1
        if status == "CLONE":
            clones.append(name)
        if status == "BLOCKED":
            disabled.append(name)
        if status == "SHORTFALL":
            shortfall.append(name)
        if status == "READY":
            qualified.append(name)
        if status in ("READY", "CONDITIONAL"):
            usable.append(name)
        tfs = raw.get("timeframes") or {}
        for tf, rec in tfs.items():
            if not rec or rec.get("status") != "OK":
                continue
            history_rows.append(
                {
                    "symbol": name,
                    "timeframe": tf,
                    "bars": rec.get("bar_count"),
                    "first": rec.get("first_bar"),
                    "last": rec.get("last_bar"),
                    "calendar_span": rec.get("calendar_span"),
                    "quality": rec.get("coverage") or rec.get("qualification"),
                    "probe_stage": raw.get("probe_stage") or ("B" if tf != "D1" else "A"),
                }
            )

    clone_groups = dict((k, v) for k, v in groups.items() if len(v) >= 2)
    equivalence = {
        "map_id": "SYMBOL_EQUIVALENCE_MAP_V1",
        "source": "V4_SPEC+V5_LIVE",
        "n_symbols": len(assets),
        "n_underlyings": len(groups),
        "n_clone_groups": len(clone_groups),
        "note": "Same economic_underlying is not a new information set. GOLD_FUTURE and SI_FUTURE are CFDs.",
        "groups": dict((k, v) for k, v in sorted(groups.items())),
        "clone_groups": clone_groups,
        "named_cfd_clones": CLONE_NAME,
    }
    dump_json(os.path.join(UNI_DIR, "SYMBOL_EQUIVALENCE_MAP_V1.json"), equivalence)

    universe = {
        "universe_id": "MT5_UNIVERSE_V5",
        "utc": now(),
        "package": live.get("package"),
        "maxbars": live.get("maxbars"),
        "total_symbols": len(assets),
        "usable_symbols": len(usable),
        "qualified_symbols": len(qualified),
        "clones": len(clones),
        "disabled": len(disabled),
        "shortfall": len(shortfall),
        "status_counts": dict(status_counts),
        "asset_class_counts": dict(class_counts),
        "instrument_type_counts": dict(type_counts),
        "true_options": 0,
        "true_futures": 0,
        "independent_underlyings": len(groups),
        "new_asset_class": ["AGRICULTURAL_CFD", "EQUITY_CFD_BASKET", "BOND_CFD"],
        "FINAL_OOS_TOUCHED": False,
        "overwrite_20260825": False,
        "overwrite_20260828": False,
        "ticks": live.get("ticks") or [],
        "assets": assets,
    }
    dump_json(os.path.join(UNI_DIR, "MT5_UNIVERSE_V5.json"), universe)
    dump_json(
        os.path.join(UNI_DIR, "MT5_HISTORY_V5.json"),
        {
            "matrix_id": "MT5_HISTORY_DEPTH_MATRIX_V5",
            "utc": now(),
            "n": len(history_rows),
            "note": "Stage A: first ~190 have deep TFs. Remaining are metadata or D1-2000 only.",
            "rows": history_rows,
        },
    )
    dump_json(
        os.path.join(UNI_DIR, "STAGE_B_CANDIDATES.json"),
        {
            "utc": now(),
            "symbols": [
                "COTTON#2",
                "COCOA",
                "COFFEE_C",
                "CORN",
                "SOYBEAN",
                "SUGAR#11",
                "WHEAT",
                "EURO-BUND",
                "JAPAN_BOND",
                "ALUMINIUM_SPOT",
                "NICKEL_SPOT",
                "US_2000",
                "AUS_200",
                "CHINA_A50",
                "HK_50",
                "FRANCE_40",
                "ITALY_40",
                "SPAIN35",
                "SWISS_20",
                "NED_25",
                "CANADA_60",
                "VIX",
            ],
            "reason": "New class or regional index not in V4 READY set. Not 638 stock clones.",
        },
    )
    print("UNI_FINAL", len(assets), dict(status_counts))
    print("CLASS", dict(class_counts))
    print("TYPE", dict(type_counts))
    print("UNDERLYINGS", len(groups), "CLONE_GROUPS", len(clone_groups))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
