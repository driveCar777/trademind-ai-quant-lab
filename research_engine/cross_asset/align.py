"""Four-way D1 inner join. No fill. Does not invent dates."""
from __future__ import print_function

from research_engine.cross_asset import (
    ALIGN_ID,
    ALIGNED_END,
    ALIGNED_N,
    ALIGNED_START,
    OOS_START,
    PARENTS,
    RESEARCH_END,
    SYMBOLS,
    VALIDATION_END,
)
from research_engine.errors import ContractMismatch
from research_protocol.bars import load_dataset
from research_protocol.hashing import canonical_hash


LOGICAL = {
    "tm-market-GOLD-D1-20260825-000001": "GOLD",
    "tm-market-EURUSD-D1-20260825-000001": "EURUSD",
    "tm-market-USDJPY-D1-20260825-000001": "USDJPY",
    "tm-market-OIL-D1-20260825-000001": "OIL",
}


def date_key(timestamp_utc):
    if not timestamp_utc:
        return None
    return timestamp_utc[:10]


def role_of_date(date):
    if date is None:
        return None
    if date < ALIGNED_START:
        return None
    if date <= RESEARCH_END:
        return "research"
    if date <= VALIDATION_END:
        return "validation"
    if date >= OOS_START:
        return "final_oos"
    return None


def _slim(bar):
    return {
        "timestamp_utc": bar.get("timestamp_utc"),
        "open": bar.get("open"),
        "high": bar.get("high"),
        "low": bar.get("low"),
        "close": bar.get("close"),
        "spread": bar.get("spread"),
        "tick_volume": bar.get("tick_volume"),
    }


def index_by_date(bars):
    out = {}
    for bar in bars:
        key = date_key(bar.get("timestamp_utc"))
        if key is None:
            continue
        if key in out:
            raise ContractMismatch("CONTRACT_MISMATCH")
        out[key] = bar
    return out


def load_parents(market_root, dataset_ids=None):
    import os

    wanted = list(dataset_ids or PARENTS)
    dir_map = {}
    for dataset_id in wanted:
        dir_map[dataset_id] = os.path.join(market_root, dataset_id)
    return load_parents_from_dirs(dir_map)


def load_parents_from_dirs(dir_map):
    """dir_map: dataset_id -> directory."""
    loaded = {}
    hashes = {}
    for dataset_id, folder in dir_map.items():
        logical = LOGICAL.get(dataset_id)
        if logical is None:
            raise ContractMismatch("CONTRACT_MISMATCH")
        manifest, bars, sha = load_dataset(folder)
        if manifest.get("dataset_id") != dataset_id:
            raise ContractMismatch("CONTRACT_MISMATCH")
        if manifest.get("timezone") != "UTC":
            raise ContractMismatch("CONTRACT_MISMATCH")
        if int(manifest.get("row_count") or 0) != 2000:
            raise ContractMismatch("CONTRACT_MISMATCH")
        for bar in bars:
            ts = bar.get("timestamp_utc") or ""
            if not ts.endswith("T00:00:00Z"):
                raise ContractMismatch("CONTRACT_MISMATCH")
        loaded[logical] = index_by_date(bars)
        hashes[dataset_id] = sha
    if set(loaded.keys()) != set(SYMBOLS):
        raise ContractMismatch("CONTRACT_MISMATCH")
    return loaded, hashes


def build_alignment(loaded, parent_hashes):
    sets = {}
    for name in SYMBOLS:
        sets[name] = set(loaded[name].keys())
    common = sets["GOLD"] & sets["EURUSD"] & sets["USDJPY"] & sets["OIL"]
    dates = sorted(common)
    if len(dates) != ALIGNED_N:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if dates[0] != ALIGNED_START or dates[-1] != ALIGNED_END:
        raise ContractMismatch("CONTRACT_MISMATCH")
    dropped = {}
    for name in SYMBOLS:
        dropped[name] = sorted(sets[name] - common)
    rows = []
    for date in dates:
        rec = {"date": date, "role": role_of_date(date)}
        for name in SYMBOLS:
            rec[name] = _slim(loaded[name][date])
        rows.append(rec)
    pack = {
        "align_id": ALIGN_ID,
        "method": "INNER_JOIN_ALL_FOUR",
        "align_key": "UTC_DATE",
        "n": len(rows),
        "start": dates[0],
        "end": dates[-1],
        "parent_hashes": parent_hashes,
        "dropped_days": dropped,
        "rows": rows,
    }
    pack["align_hash"] = canonical_hash(
        {
            "dates": dates,
            "dropped_days": dropped,
            "parent_hashes": parent_hashes,
            "n": len(dates),
        }
    )
    return pack


def oos_exists(pack):
    n = 0
    first = None
    last = None
    for row in pack.get("rows") or []:
        if row.get("role") == "final_oos":
            n += 1
            if first is None:
                first = row.get("date")
            last = row.get("date")
    return {"exists": n > 0, "n": n, "start": first, "end": last}


def iter_role(pack, role):
    from research_engine.cross_asset.contract import deny_final_oos

    deny_final_oos(role)
    out = []
    for row in pack.get("rows") or []:
        if row.get("role") == role:
            out.append(row)
    return out
