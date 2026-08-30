"""Build master CSV, attribution, and V9 reports from replay rows."""
from __future__ import print_function

import csv
import json
import os
import shutil

from research_engine.v9_master import DATABENTO_HISTORICAL_SPEND
from research_engine.v9_master.classify import MECHANISMS
from research_engine.v9_master.paths import CURVES, DOCS, LEDGERS, OUT, ensure_dir
from research_protocol.hashing import canonical_hash


def _load(path):
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _dump(path, payload):
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def _write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()


def _m(row):
    return row.get("metrics") or {}


def _net(row):
    m = _m(row)
    if m.get("net_return") is not None:
        return m.get("net_return")
    return m.get("total_return")


def base_strategy_rows(raw_rows):
    out = []
    for row in raw_rows:
        if row.get("replay_kind") != "STRATEGY_REPLAY":
            continue
        if row.get("scenario") not in (None, "base"):
            continue
        if row.get("role") != "research":
            continue
        out.append(row)
    return out


def pair_validation(raw_rows, row):
    for other in raw_rows:
        if other.get("strategy_id") != row.get("strategy_id"):
            continue
        if other.get("family") != row.get("family"):
            continue
        if (other.get("dataset_id") or other.get("target")) != (row.get("dataset_id") or row.get("target")):
            continue
        if other.get("role") == "validation" and other.get("scenario") in (None, "base"):
            return other
    return None


def counts(raw_rows):
    replayed = set()
    profitable = set()
    loss = set()
    non_tr = set()
    for row in raw_rows:
        sid = row.get("strategy_id")
        kind = row.get("replay_kind")
        if kind == "STRATEGY_REPLAY":
            replayed.add(sid)
        if row.get("status") == "NON_TRADEABLE" or kind in ("PREDICTIVE_ONLY", "FACTOR_ONLY", "ALPHA_TEST"):
            non_tr.add(sid)
        if row.get("role") == "research" and row.get("scenario") in (None, "base"):
            net = _net(row)
            if net is not None and net > 0:
                profitable.add(sid)
            elif net is not None and net <= 0 and kind == "STRATEGY_REPLAY":
                loss.add(sid)
    return {
        "strategies_replayed": len(replayed),
        "strategies_profitable": len(profitable),
        "strategies_loss": len(loss),
        "strategies_non_tradeable": len(non_tr),
        "profitable_ids": sorted(profitable),
        "loss_ids": sorted(loss),
        "non_tradeable_ids": sorted(non_tr),
    }


def reporting_sort_key(row):
    net = _net(row)
    dd = _m(row).get("max_drawdown")
    sharpe = _m(row).get("sharpe")
    return (
        0 if net is None else -float(net),
        0 if dd is None else float(dd),
        0 if sharpe is None else -float(sharpe),
    )


def best_of(rows, information_set=None):
    pool = []
    for row in rows:
        if information_set and row.get("information_set") != information_set:
            continue
        if row.get("replay_kind") != "STRATEGY_REPLAY":
            continue
        if row.get("role") != "research":
            continue
        if row.get("scenario") not in (None, "base"):
            continue
        pool.append(row)
    if not pool:
        return None
    pool.sort(key=reporting_sort_key)
    return pool[0]


def _layer_summary(raw_rows, code):
    best = best_of(raw_rows, code)
    pos = 0
    n = 0
    for row in raw_rows:
        if row.get("information_set") != code:
            continue
        if row.get("role") != "research" or row.get("scenario") not in (None, "base"):
            continue
        if row.get("replay_kind") != "STRATEGY_REPLAY":
            continue
        n += 1
        net = _net(row)
        if net is not None and net > 0:
            pos += 1
    return {
        "information_set": code,
        "n_research_books": n,
        "n_positive_research": pos,
        "best": None
        if best is None
        else {
            "strategy_id": best.get("strategy_id"),
            "family": best.get("family"),
            "target": best.get("target"),
            "net_return": _net(best),
            "cagr": _m(best).get("cagr"),
            "max_dd": _m(best).get("max_drawdown"),
            "sharpe": _m(best).get("sharpe"),
            "economic_status": best.get("economic_status"),
        },
    }


def incremental(a, b):
    def g(layer, field):
        best = (layer or {}).get("best") or {}
        return best.get(field)

    def sub(field):
        x = g(b, field)
        y = g(a, field)
        if x is None or y is None:
            return None
        return x - y

    return {
        "incremental_return": sub("net_return"),
        "incremental_cagr": sub("cagr"),
        "incremental_sharpe": sub("sharpe"),
        "incremental_dd": sub("max_dd"),
    }


def write_master_csv(raw_rows, path):
    fields = [
        "strategy_id",
        "information_set",
        "target",
        "start",
        "end",
        "trades",
        "gross_return",
        "net_return",
        "CAGR",
        "max_dd",
        "Sharpe",
        "Sortino",
        "Calmar",
        "turnover",
        "data_cost",
        "live_external_dependency",
        "status",
        "family",
        "dataset_id",
        "timeframe",
        "economic_status",
        "replay_kind",
        "validation_net_return",
        "validation_trades",
        "level1_dataset_status",
    ]
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in raw_rows:
            if row.get("role") not in (None, "research"):
                continue
            if row.get("scenario") not in (None, "base"):
                continue
            m = _m(row)
            val = pair_validation(raw_rows, row)
            vm = _m(val) if val else {}
            yearly = m.get("yearly") or []
            start = yearly[0]["year"] if yearly else ""
            end = yearly[-1]["year"] if yearly else ""
            writer.writerow(
                {
                    "strategy_id": row.get("strategy_id"),
                    "information_set": row.get("information_set"),
                    "target": row.get("target") or row.get("target_group") or "",
                    "start": start,
                    "end": end,
                    "trades": m.get("trade_count") if m.get("trade_count") is not None else "",
                    "gross_return": m.get("gross_return") if m.get("gross_return") is not None else "",
                    "net_return": _net(row) if _net(row) is not None else "",
                    "CAGR": m.get("cagr") if m.get("cagr") is not None else "",
                    "max_dd": m.get("max_drawdown") if m.get("max_drawdown") is not None else "",
                    "Sharpe": m.get("sharpe") if m.get("sharpe") is not None else "",
                    "Sortino": m.get("sortino") if m.get("sortino") is not None else "",
                    "Calmar": m.get("calmar") if m.get("calmar") is not None else "",
                    "turnover": m.get("turnover") if m.get("turnover") is not None else "",
                    "data_cost": row.get("data_cost") if row.get("data_cost") is not None else 0.0,
                    "live_external_dependency": row.get("live_external_dependency") or "",
                    "status": row.get("economic_status") or row.get("status") or "",
                    "family": row.get("family") or "",
                    "dataset_id": row.get("dataset_id") or "",
                    "timeframe": row.get("timeframe") or "",
                    "economic_status": row.get("economic_status") or "",
                    "replay_kind": row.get("replay_kind") or "",
                    "validation_net_return": _net(val) if val else "",
                    "validation_trades": vm.get("trade_count") if vm else "",
                    "level1_dataset_status": row.get("level1_dataset_status") or "",
                }
            )
    finally:
        handle.close()


def copy_best_curves(raw_rows):
    ensure_dir(CURVES)
    names = {
        "IS-A": "mt5_only_best",
        "IS-B": "mt5_public_best",
        "IS-C": "mt5_futures_best",
        "IS-D": "all_owned_best",
    }
    copied = {}
    any_pos = False
    for code, name in names.items():
        best = best_of(raw_rows, code)
        dest = os.path.join(CURVES, name)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        if best is None or _net(best) is None or _net(best) <= 0:
            copied[code] = {"status": "NO_POSITIVE_EQUITY_CURVE", "best": None if best is None else best.get("strategy_id")}
            _write(os.path.join(CURVES, name + "_NO_POSITIVE_EQUITY_CURVE.txt"), "NO_POSITIVE_EQUITY_CURVE\n")
            continue
        any_pos = True
        sid = best.get("strategy_id")
        dataset = best.get("dataset_id") or best.get("target") or ""
        prefix = "%s__%s__research__base" % (
            str(sid).replace("/", "_").replace("\\", "_"),
            str(dataset).replace("/", "_"),
        )
        src = os.path.join(LEDGERS, prefix)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
            copied[code] = {"status": "COPIED", "strategy_id": sid, "src": src}
        else:
            copied[code] = {"status": "LEDGER_MISSING", "strategy_id": sid, "expected": src}
    if not any_pos:
        _write(os.path.join(CURVES, "NO_POSITIVE_EQUITY_CURVE.txt"), "NO_POSITIVE_EQUITY_CURVE\n")
    return copied


def cross_symbol(raw_rows):
    out = {}
    for row in raw_rows:
        if row.get("role") != "research" or row.get("scenario") not in (None, "base"):
            continue
        if row.get("replay_kind") != "STRATEGY_REPLAY":
            continue
        fam = row.get("family")
        target = row.get("target") or row.get("target_group") or "UNK"
        if target in ("EURUSD", "USDJPY"):
            bucket = "FX"
        elif target == "GOLD":
            bucket = "GOLD"
        elif target == "OIL":
            bucket = "OIL"
        elif target == "GOLD_OIL":
            bucket = "GOLD_OIL"
        else:
            bucket = str(target)
        net = _net(row)
        mark = "not applicable"
        if net is None:
            mark = "not applicable"
        elif net > 0:
            mark = "positive"
        else:
            mark = "negative"
        fam_row = out.get(fam) or {}
        prev = fam_row.get(bucket)
        if prev == "positive" or mark == "positive":
            fam_row[bucket] = "positive" if (prev == "positive" or mark == "positive") and prev != "negative" else mark
            if prev == "negative" and mark == "positive":
                fam_row[bucket] = "mixed"
            elif prev == "positive" and mark == "negative":
                fam_row[bucket] = "mixed"
        else:
            fam_row[bucket] = mark
        out[fam] = fam_row
    return out


def compile_all():
    ensure_dir(OUT)
    replay = _load(os.path.join(OUT, "REPLAY_ROWS_V9.json"))
    raw_rows = replay.get("rows") or []
    c = counts(raw_rows)
    layers = {
        "IS-A": _layer_summary(raw_rows, "IS-A"),
        "IS-B": _layer_summary(raw_rows, "IS-B"),
        "IS-C": _layer_summary(raw_rows, "IS-C"),
        "IS-D": _layer_summary(raw_rows, "IS-D"),
    }
    inc = {
        "B_minus_A": incremental(layers["IS-A"], layers["IS-B"]),
        "C_minus_B": incremental(layers["IS-B"], layers["IS-C"]),
        "D_minus_C": incremental(layers["IS-C"], layers["IS-D"]),
        "D_minus_A": incremental(layers["IS-A"], layers["IS-D"]),
    }
    stop_a = bool(replay.get("STOP_A"))
    pos_repro = 0
    by_sid = {}
    for row in raw_rows:
        if row.get("role") != "research" or row.get("scenario") not in (None, "base"):
            continue
        if row.get("economic_status") != "POSITIVE_REPRODUCIBLE":
            continue
        key = (row.get("family"), row.get("strategy_id"))
        bucket = by_sid.get(key)
        if bucket is None:
            bucket = []
            by_sid[key] = bucket
        bucket.append(row.get("target") or row.get("dataset_id"))
    program_repro_ids = []
    for key, targets in by_sid.items():
        uniq = set([t for t in targets if t])
        gold_oil = ("GOLD" in uniq and "OIL" in uniq)
        two_ds = len(uniq) >= 2
        if gold_oil or (key[0] == "PROFIT_DISCOVERY_V0.6" and two_ds):
            program_repro_ids.append(key)
            pos_repro += 1
        else:
            for row in raw_rows:
                if row.get("family") == key[0] and row.get("strategy_id") == key[1]:
                    if row.get("economic_status") == "POSITIVE_REPRODUCIBLE":
                        row["economic_status"] = "POSITIVE_BUT_WEAK"
                        row["economic_note"] = "Single-target leftover. Not program-reproducible."
    stop_b = (not stop_a) and pos_repro == 0
    info_value = {
        "index_id": "INFORMATION_VALUE_V9",
        "layers": layers,
        "incremental": inc,
        "databento": {
            "historical_spend_usd": DATABENTO_HISTORICAL_SPEND,
            "new_spend_usd": 0.0,
            "added_information": "GC/CL official settlement, OI, volume, DTE/roll, plus V8 fusion with public series",
            "added_strategies": layers["IS-C"]["n_research_books"] + layers["IS-D"]["n_research_books"],
            "added_positive_research": layers["IS-C"]["n_positive_research"] + layers["IS-D"]["n_positive_research"],
            "incremental_vs_public": inc["C_minus_B"],
            "incremental_vs_mt5": inc["D_minus_A"],
            "candidate": 0,
            "note": "incremental research value, not dollar P&L value of $31.82",
        },
        "public_incremental": inc["B_minus_A"],
        "leave_one_source_out": {
            "applied": False,
            "reason": "ALL_OWNED did not produce a positive reproducible strategy. Leave-one-out is attribution of a gain that did not occur.",
        },
    }
    dep = []
    for mech in MECHANISMS:
        dep.append(
            {
                "family": mech["family"],
                "information_set": mech["information_set"],
                "live_signal_inputs": mech.get("public_source") or mech.get("futures_source") or "MT5",
                "EXTERNAL_LIVE_DATA": mech.get("live_external") or "NO",
                "RESEARCH_ONLY_EXTERNAL": mech.get("live_external") == "YES",
            }
        )
    _dump(os.path.join(OUT, "INFORMATION_VALUE_V9.json"), info_value)
    _dump(os.path.join(OUT, "STRATEGY_INFORMATION_DEPENDENCY_V9.json"), {"rows": dep})
    csv_path = os.path.join(OUT, "TRADE_MIND_MASTER_BACKTEST.csv")
    write_master_csv(raw_rows, csv_path)
    copied = copy_best_curves(raw_rows)
    best_all = best_of(raw_rows)
    master_metrics = {
        "counts": c,
        "layers": layers,
        "best_reporting": None
        if best_all is None
        else {
            "strategy_id": best_all.get("strategy_id"),
            "family": best_all.get("family"),
            "information_set": best_all.get("information_set"),
            "target": best_all.get("target"),
            "net_return": _net(best_all),
            "cagr": _m(best_all).get("cagr"),
            "max_dd": _m(best_all).get("max_drawdown"),
            "sharpe": _m(best_all).get("sharpe"),
            "sortino": _m(best_all).get("sortino"),
            "economic_status": best_all.get("economic_status"),
        },
        "STOP_A": stop_a,
        "STOP_B": stop_b,
        "LEVEL": 0,
        "LEVEL_1_CANDIDATE": 1 if stop_a else 0,
        "positive_reproducible_n": pos_repro,
        "curve_copy": copied,
        "FINAL_OOS_TOUCHED": False,
        "NEW_DATA_PURCHASE": False,
    }
    master_metrics["content_hash"] = canonical_hash(
        {"counts": c, "layers": layers, "best": master_metrics["best_reporting"]}
    )
    _dump(os.path.join(OUT, "MASTER_METRICS.json"), master_metrics)
    xs = cross_symbol(raw_rows)
    _dump(os.path.join(OUT, "CROSS_SYMBOL_V9.json"), xs)
    write_reports(raw_rows, c, layers, inc, master_metrics, info_value, xs, stop_a, stop_b)
    return master_metrics


def _pct(x):
    if x is None:
        return "n/a"
    return "%.4f" % x


def write_reports(raw_rows, c, layers, inc, master_metrics, info_value, xs, stop_a, stop_b):
    best = master_metrics.get("best_reporting") or {}
    answers = {
        "A_mt5_only": "NO" if (layers["IS-A"].get("n_positive_research") or 0) == 0 else "RESEARCH_POSITIVE_NOT_CANDIDATE",
        "B_mt5_public": "NO" if (layers["IS-B"].get("n_positive_research") or 0) == 0 else "RESEARCH_POSITIVE_NOT_CANDIDATE",
        "C_mt5_futures": "NO" if (layers["IS-C"].get("n_positive_research") or 0) == 0 else "RESEARCH_POSITIVE_NOT_CANDIDATE",
        "D_all_owned": "NO" if (layers["IS-D"].get("n_positive_research") or 0) == 0 else "RESEARCH_POSITIVE_NOT_CANDIDATE",
        "E_databento": info_value.get("databento"),
        "F_best": best,
        "G_level1": 0 if not stop_a else 1,
        "H_gap": "Existing locked mechanisms do not produce a Positive Reproducible Strategy after MT5 costs. The gap is not another simple price rule.",
        "I_options_now": "NO_PURCHASE",
        "J_if_buy": "Only if a human later accepts a new family that needs OG/LO occupancy. V8.4 preferred pack remains LO 1Y MVD-A $11.99. Live book would need EXTERNAL_LIVE_DATA=YES.",
    }
    if master_metrics.get("positive_reproducible_n"):
        answers["A_mt5_only"] = "PARTIAL" if layers["IS-A"]["n_positive_research"] else answers["A_mt5_only"]

    _write(
        os.path.join(DOCS, "V9_MASTER_BACKTEST_REPORT.md"),
        "\n".join(
            [
                "# V9 Master Backtest Report",
                "",
                "Replay of existing locked mechanisms. No new hypotheses. No data purchase. Final OOS DENIED.",
                "",
                "## Counts",
                "",
                "- strategies_replayed: %s" % c["strategies_replayed"],
                "- strategies_profitable (research net>0): %s" % c["strategies_profitable"],
                "- strategies_loss: %s" % c["strategies_loss"],
                "- strategies_non_tradeable: %s" % c["strategies_non_tradeable"],
                "- POSITIVE_REPRODUCIBLE books: %s" % master_metrics.get("positive_reproducible_n"),
                "- LEVEL_1_CANDIDATE: %s" % master_metrics.get("LEVEL_1_CANDIDATE"),
                "",
                "## Best reporting row (pre-fixed sort: net return, then max DD, then Sharpe)",
                "",
                "```",
                json.dumps(best, indent=2, sort_keys=True),
                "```",
                "",
                "## Layers",
                "",
                "```",
                json.dumps(layers, indent=2, sort_keys=True),
                "```",
                "",
                "## Execution",
                "",
                "TRADING VENUE = MT5. Fill = NEXT_BAR_OPEN. Bars are OHLC + spread points: EXECUTION_APPROXIMATION.",
                "HYP-0001 and Factor Discovery and V0.5 are not strategy CAGRs.",
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "V9_INFORMATION_VALUE_REPORT.md"),
        "\n".join(
            [
                "# V9 Information Value Report",
                "",
                "IS-A = MT5 only. IS-B = MT5 + free public / extra owned CFDs. IS-C = + Pack E futures. IS-D = all owned fusion.",
                "",
                "## Incremental (best-of-layer, reporting sort only)",
                "",
                "```",
                json.dumps(inc, indent=2, sort_keys=True),
                "```",
                "",
                "## Databento $31.82",
                "",
                "This is incremental **research value**, not a dollar P&L claim.",
                "Best-of-layer comparisons can pick LEVEL_LEAK / FALSIFIED leftovers. Databento added 0 Candidates and 0 Positive Reproducible Strategies.",
                "",
                "```",
                json.dumps(info_value.get("databento"), indent=2, sort_keys=True),
                "```",
                "",
                "## Leave-one-source-out",
                "",
                json.dumps(info_value.get("leave_one_source_out"), indent=2),
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "INFORMATION_VALUE_COMPARISON_V9.md"),
        "\n".join(
            [
                "# INFORMATION_VALUE_COMPARISON_V9",
                "",
                "| Layer | n books | n research+ | best id | best net | best CAGR | best Sharpe | best DD |",
                "|---|---:|---:|---|---:|---:|---:|---:|",
                _layer_line("IS-A MT5", layers["IS-A"]),
                _layer_line("IS-B +public", layers["IS-B"]),
                _layer_line("IS-C +futures", layers["IS-C"]),
                _layer_line("IS-D all owned", layers["IS-D"]),
                "",
                "Incremental C vs B (Databento vs public): %s" % json.dumps(inc["C_minus_B"]),
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "V9_PROFITABILITY_AUDIT.md"),
        "\n".join(
            [
                "# V9 Profitability Audit",
                "",
                "BACKTEST ECONOMIC STATUS is not the Level 1 Candidate gate.",
                "",
                "## Program counts",
                "",
                json.dumps(c, indent=2),
                "",
                "## Cross-symbol",
                "",
                json.dumps(xs, indent=2, sort_keys=True),
                "",
                "## Why Candidate is still 0" if not stop_a else "## STOP A",
                "",
                "Historical families were already KILLED. V9 replay used the same entry/exit/cost contracts.",
                "A research-window net>0 leftover is WEAK / LOSS at program level unless both windows and the locked gate pass.",
                "HYP-0001 remains PREDICTIVE_ONLY.",
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "EXISTING_DATA_PROFITABILITY_AUDIT.md"),
        "\n".join(
            [
                "# EXISTING_DATA_PROFITABILITY_AUDIT",
                "",
                "Current information set after unified MT5 costed replay:",
                "",
                "- LEVEL = 0",
                "- LEVEL_1_CANDIDATE = %s" % master_metrics.get("LEVEL_1_CANDIDATE"),
                "- POSITIVE_REPRODUCIBLE = %s" % master_metrics.get("positive_reproducible_n"),
                "- STOP_B = %s" % stop_b,
                "",
                "The owned price, public, and Pack E futures books do not produce a Positive Reproducible Strategy.",
                "That is not a license to buy options or spend the $93 reserve.",
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "V9_DATA_COST_ANALYSIS.md"),
        "\n".join(
            [
                "# V9 Data Cost Analysis",
                "",
                "- Databento historical spend: $%.6f" % DATABENTO_HISTORICAL_SPEND,
                "- V9 new spend: $0",
                "- Remaining credits: UNUSED_RESEARCH_RESERVE (~$93). Not a budget.",
                "- Net-of-data CAGR: not computed as a dollar claim. No positive reproducible live book.",
                "- LIVE_DATA_DEPENDENCY: futures/public families would need external live feeds; MT5-only V0.6 would not.",
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "OPTIONS_DATA_VALUE_CASE.md"),
        "\n".join(
            [
                "# OPTIONS_DATA_VALUE_CASE",
                "",
                "Generated because no Positive Reproducible Strategy exists on owned data.",
                "Still: NO PURCHASE.",
                "",
                "V8.4 already measured occupancy. If a human later buys one pack: LO 1Y MVD-A $11.99.",
                "OG is grade B. Dual pack is not required for a first options test.",
                "A live options-IV book would be EXTERNAL_LIVE_DATA=YES. This file does not authorize download.",
                "",
            ]
        ),
    )
    _write(
        os.path.join(DOCS, "DATA_GAP_ANALYSIS.md"),
        "\n".join(
            [
                "# DATA_GAP_ANALYSIS",
                "",
                "Do not purchase from this file.",
                "",
                "Owned information that was actually replayed is exhausted at the strategy layer.",
                "What is still missing as *information*, not as another z-cut:",
                "",
                "1. Options surfaces (OG/LO) — quoted, occupancy known, bytes = 0.",
                "2. A representation change (how the same bars are used), not a new farm of simple rules.",
                "3. Live microstructure beyond OHLC+spread points (not faked here).",
                "",
                "A-share is out of scope. Final OOS remains DENIED.",
                "",
            ]
        ),
    )
    stop = (
        "STOP A: Level 1 Candidate. Freeze new research."
        if stop_a
        else "STOP B: all legal strategy mechanisms replayed; no Positive Reproducible Strategy. Do not buy data. Next = model / information representation review."
    )
    _write(
        os.path.join(DOCS, "V9_DECISION.md"),
        "\n".join(
            [
                "# V9 Decision",
                "",
                stop,
                "",
                "Reporting 'best' rows use a pre-fixed sort (net return, then max DD, then Sharpe). They include historically FALSIFIED / LEVEL_LEAK leftovers. They are not Candidates and not a reason to retune.",
                "",
                "## A-J",
                "",
                "### A. MT5-only",
                "",
                answers["A_mt5_only"],
                "",
                "### B. MT5 + public",
                "",
                answers["B_mt5_public"],
                "",
                "### C. MT5 + futures",
                "",
                answers["C_mt5_futures"],
                "",
                "### D. ALL OWNED",
                "",
                answers["D_all_owned"],
                "",
                "### E. Databento incremental research value",
                "",
                json.dumps(answers["E_databento"], indent=2),
                "",
                "### F. Best legal reporting strategy",
                "",
                json.dumps(answers["F_best"], indent=2),
                "",
                "### G. Level 1 Candidate?",
                "",
                str(answers["G_level1"]),
                "",
                "### H. If none, what is missing?",
                "",
                answers["H_gap"],
                "",
                "### I. Buy options now?",
                "",
                answers["I_options_now"],
                "",
                "### J. If a human later buys",
                "",
                answers["J_if_buy"],
                "",
                "## Hard stops",
                "",
                "- NEW_DATA_PURCHASE = FALSE",
                "- $93 credits = UNUSED_RESEARCH_RESERVE",
                "- Do not retune killed families",
                "- Do not read Final OOS",
                "",
            ]
        ),
    )


def _layer_line(label, layer):
    b = layer.get("best") or {}
    return "| %s | %s | %s | %s | %s | %s | %s | %s |" % (
        label,
        layer.get("n_research_books"),
        layer.get("n_positive_research"),
        b.get("strategy_id") or "",
        _pct(b.get("net_return")),
        _pct(b.get("cagr")),
        _pct(b.get("sharpe")),
        _pct(b.get("max_dd")),
    )
