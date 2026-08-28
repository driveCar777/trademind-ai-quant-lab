"""Classify frozen V11.7 mine JSONL. Does not change the backtest engine."""
from __future__ import print_function

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROWS = os.path.join(ROOT, "data", "mine", "longrun", "rows.jsonl")
OUT_DIR = os.path.join(ROOT, "data", "mine", "longrun")
REPORT = os.path.join(OUT_DIR, "CLOSEOUT.md")
DUMP = os.path.join(OUT_DIR, "closeout.json")

WATCH = (
    ("GOLD", "H1", "rsi-14-35-85"),
    ("GOLD", "M15", "rsi-14-30-80"),
    ("EURUSD", "H4", "rsi-28-32-72"),
)


def rank_row(row):
    start = int(row.get("win_start") or 9999)
    length = int(row.get("win_len") or 0)
    cyc = 0 if "|c" not in str(row.get("key") or "") else 1
    # Prefer first full-series window; later cycles are shifted repeats.
    return (cyc, 0 if length == 2000 else 1, start, -length)


def better(old, new):
    if old is None:
        return True
    return rank_row(new) < rank_row(old)


def classify(row):
    verdict = row.get("verdict") or "insufficient"
    is_p = float(row.get("is_profit") or 0)
    oos_p = float(row.get("oos_profit") or 0)
    is_dd = float(row.get("is_drawdown") or 0)
    oos_dd = float(row.get("oos_drawdown") or 0)
    is_n = int(row.get("is_trades") or 0)
    oos_n = int(row.get("oos_trades") or 0)
    patterns = []
    if is_p >= 50 and oos_p < is_p * 0.25:
        patterns.append("IS strong / OOS weak")
    if is_dd > 25 or oos_dd > 25:
        patterns.append("drawdown over limit")
    if is_n < 5 or oos_n < 5:
        patterns.append("insufficient trades")
    if oos_p <= 0 and verdict != "insufficient":
        patterns.append("OOS <= 0")
    if min(is_n, oos_n) >= 5 and min(is_n, oos_n) < 10:
        patterns.append("low sample 5-9")
    if verdict != "survived":
        return "A", patterns
    if min(is_n, oos_n) < 10:
        return "B", patterns
    if "IS strong / OOS weak" in patterns or oos_dd > 15 and is_p >= 40:
        return "D", patterns
    return "C", patterns


def neighbors_of(cid):
    parts = str(cid).split("-")
    if parts[0] != "rsi" or len(parts) != 4:
        return []
    try:
        period, osold, obuy = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        return []
    out = []
    for dp, dos, dob in ((0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0)):
        p, a, b = period + dp, osold + dos, obuy + dob
        if a >= b or p < 2:
            continue
        out.append("rsi-%s-%s-%s" % (p, a, b))
    return out


def load_canonical():
    by = {}
    verdicts = Counter()
    cycles = Counter()
    n = 0
    skipped = 0
    with open(ROWS, "r", encoding="utf-8") as fh:
        for line in fh:
            n += 1
            try:
                row = json.loads(line)
            except ValueError:
                skipped += 1
                continue
            if row.get("error") and not row.get("verdict"):
                skipped += 1
                continue
            key = "%s|%s|%s" % (row.get("symbol"), row.get("timeframe"), row.get("id"))
            if better(by.get(key), row):
                by[key] = row
            raw_key = str(row.get("key") or "")
            if "|c" in raw_key:
                cycles[raw_key.rsplit("|c", 1)[-1]] += 1
            else:
                cycles["0"] += 1
            if n % 400000 == 0:
                print("scanned", n, "unique", len(by), flush=True)
    return by, n, skipped, cycles, verdicts


def main():
    if not os.path.isfile(ROWS):
        print("NO_ROWS")
        return 1
    print("reading", ROWS, flush=True)
    by, n, skipped, cycles, _ = load_canonical()
    buckets = {"A": [], "B": [], "C": [], "D": []}
    patterns = Counter()
    verdicts = Counter()
    for key, row in by.items():
        bucket, pats = classify(row)
        row["_bucket"] = bucket
        row["_patterns"] = pats
        buckets[bucket].append(row)
        verdicts[row.get("verdict") or "na"] += 1
        for p in pats:
            patterns[p] += 1
    for bucket in buckets:
        buckets[bucket].sort(key=lambda r: float(r.get("is_score") or -999), reverse=True)

    plateau = []
    island = []
    for row in buckets["B"] + buckets["C"]:
        cid = row.get("id")
        if not str(cid).startswith("rsi-"):
            continue
        ok = 0
        seen = []
        for nid in neighbors_of(cid):
            nkey = "%s|%s|%s" % (row.get("symbol"), row.get("timeframe"), nid)
            other = by.get(nkey)
            if not other:
                continue
            nb, _pats = classify(other)
            seen.append((nid, nb, other.get("verdict"), other.get("is_profit"), other.get("oos_profit")))
            if nb in ("B", "C"):
                ok += 1
        item = {
            "center": "%s %s %s" % (row.get("symbol"), row.get("timeframe"), cid),
            "ok_neighbors": ok,
            "neighbors": seen,
        }
        if ok >= 2:
            plateau.append(item)
        elif seen and ok == 0:
            island.append(item)

    review = []
    used = set()

    def add_review(row, why):
        key = "%s|%s|%s" % (row.get("symbol"), row.get("timeframe"), row.get("id"))
        if key in used or row is None:
            return
        used.add(key)
        review.append({
            "symbol": row.get("symbol"),
            "timeframe": row.get("timeframe"),
            "strategy": row.get("strategy"),
            "params": row.get("params"),
            "id": row.get("id"),
            "IS_profit": row.get("is_profit"),
            "IS_drawdown": row.get("is_drawdown"),
            "IS_score": row.get("is_score"),
            "OOS_profit": row.get("oos_profit"),
            "OOS_drawdown": row.get("oos_drawdown"),
            "trade_count_is": row.get("is_trades"),
            "trade_count_oos": row.get("oos_trades"),
            "classification": row.get("_bucket"),
            "reason": why,
            "win_start": row.get("win_start"),
            "win_len": row.get("win_len"),
        })

    for sym, tf, cid in WATCH:
        row = by.get("%s|%s|%s" % (sym, tf, cid))
        if row:
            add_review(row, "named watch; treat as manual ledger read only, not a strategy")
    for row in buckets["C"][:8]:
        if len(review) >= 5:
            break
        add_review(row, "survived with both sides >=10 trades on canonical window; still not a buy signal")
    for row in buckets["B"]:
        if len(review) >= 5:
            break
        if row.get("symbol") in ("GOLD", "EURUSD") and str(row.get("timeframe")) in ("H1", "H4", "M15"):
            add_review(row, "survived but LOW SAMPLE (5-9 fills on a side)")

    summary = {
        "lines_scanned": n,
        "lines_skipped": skipped,
        "unique_symbol_tf_id": len(by),
        "cycle_line_counts": dict(cycles),
        "canonical_verdicts": dict(verdicts),
        "bucket_counts": {k: len(v) for k, v in buckets.items()},
        "pattern_counts": dict(patterns),
        "review": review,
        "plateau_n": len(plateau),
        "island_n": len(island),
        "plateau_examples": plateau[:12],
        "island_examples": island[:12],
        "A_examples": [
            {
                "id": r.get("id"),
                "symbol": r.get("symbol"),
                "tf": r.get("timeframe"),
                "verdict": r.get("verdict"),
                "is": r.get("is_profit"),
                "oos": r.get("oos_profit"),
                "patterns": r.get("_patterns"),
            }
            for r in buckets["A"][:15]
        ],
        "C_all": [
            {
                "id": r.get("id"),
                "symbol": r.get("symbol"),
                "tf": r.get("timeframe"),
                "is": r.get("is_profit"),
                "dd": r.get("is_drawdown"),
                "oos": r.get("oos_profit"),
                "oos_dd": r.get("oos_drawdown"),
                "n": [r.get("is_trades"), r.get("oos_trades")],
                "score": r.get("is_score"),
            }
            for r in buckets["C"][:30]
        ],
        "D_examples": [
            {
                "id": r.get("id"),
                "symbol": r.get("symbol"),
                "tf": r.get("timeframe"),
                "is": r.get("is_profit"),
                "oos": r.get("oos_profit"),
                "oos_dd": r.get("oos_drawdown"),
                "patterns": r.get("_patterns"),
            }
            for r in buckets["D"][:20]
        ],
    }
    with open(DUMP, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("WROTE", DUMP)
    print("unique", len(by), "A", len(buckets["A"]), "B", len(buckets["B"]), "C", len(buckets["C"]), "D", len(buckets["D"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
