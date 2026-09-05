"""ML1 daily forward run. Usage:

    python -m research_engine.ml1_live.daily [--asof YYYY-MM-DD] [--capital 5000000] [--force-score] [--no-holders] [--skip-fetch]

Order: calendar/basics/bars -> margin -> (holders weekly, index monthly) -> live pack -> features -> shadow ledger -> today's list (if signal day or --force-score) -> STATUS.json.
Never sends orders. Never writes into frozen datasets.
"""
from __future__ import print_function

import argparse
import datetime
import json
import os
import sys
import time

# env for V23/V24/V25 modules must be set before they are imported anywhere in this process
from research_engine.ml1_live import (  # noqa: E402
    CALENDAR_CSV, DEFAULT_CAPITAL, FEATURES, HOLDERS_NORM, HOLDERS_RAW, LIVE, MARGIN_NORM, SIGNALS, STATUS, ensure_live,
)


def _set_env(asof):
    os.environ["TRADEMIND_MARGIN_END"] = asof
    os.environ["TRADEMIND_MARGIN_NORM"] = MARGIN_NORM
    os.environ["TRADEMIND_MARGIN_CALENDAR"] = CALENDAR_CSV
    os.environ["TRADEMIND_HOLDERS_RAW"] = HOLDERS_RAW
    os.environ["TRADEMIND_HOLDERS_NORM"] = HOLDERS_NORM
    os.environ["TRADEMIND_HOLDERS_NOTICE_CUTOFF"] = asof
    os.environ["TRADEMIND_V25_FEAT_CACHE"] = FEATURES


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=datetime.date.today().isoformat())
    ap.add_argument("--capital", type=float, default=DEFAULT_CAPITAL)
    ap.add_argument("--force-score", action="store_true")
    ap.add_argument("--no-holders", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true", help="use data already on disk (no BaoStock/Eastmoney)")
    a = ap.parse_args(argv)
    ensure_live()
    _set_env(a.asof)
    t0 = time.time()
    status = {"asof_requested": a.asof, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "steps": {}}

    from research_engine.ml1_live import layers, panel
    from research_engine.ml1_live.ledger import chain_signal_indices, update_ledger
    from research_engine.ml1_live.score import eligibility, features_for, score_session

    # 1-2 calendar, basics, bars
    if a.skip_fetch:
        equities = panel.load_live_equities()
        cal = panel.load_live_calendar()
        days = panel.trading_days(cal)
        asof_session = max(d for d in days if d <= a.asof)
        live_sessions = [d for d in days if d > panel.FROZEN_END]
        status["steps"]["fetch"] = "skipped"
    else:
        equities, live_sessions, asof_session, st = panel.refresh_all(asof=a.asof)
        status["steps"]["bars"] = st
        _set_env(asof_session)
        # 3 margin (per-day files, idempotent)
        try:
            status["steps"]["margin"] = layers.refresh_margin(asof_session)
        except Exception as e:  # noqa
            status["steps"]["margin"] = {"error": str(e)[:200]}
        # 4 holders weekly (file age), index monthly
        if not a.no_holders:
            try:
                status["steps"]["holders"] = layers.refresh_holders(asof_session, [e["symbol"] for e in equities])
            except Exception as e:  # noqa
                status["steps"]["holders"] = {"error": str(e)[:200]}
        try:
            status["steps"]["index"] = layers.refresh_index(asof_session)
        except Exception as e:  # noqa
            status["steps"]["index"] = {"error": str(e)[:200]}
        status["steps"]["annual"] = layers.annual_status(asof_session)
    status["asof_session"] = asof_session

    # 5 live pack
    pack = panel.build_live_pack(equities, live_sessions, asof_session)
    status["live_pack"] = pack["meta"]
    # 6 layers compiled against this pack + features
    stamp = os.path.join(FEATURES, "PACK_STAMP.json")
    prev = json.load(open(stamp, encoding="utf-8")) if os.path.isfile(stamp) else {}
    changed = prev.get("live_hash") != pack["meta"]["live_hash"] or prev.get("n_dates") != len(pack["dates"])
    if changed or not os.path.isfile(os.path.join(MARGIN_NORM, "RZYE.npy")):
        layers.compile_margin(pack)
        layers.compile_holders(pack)
    feats, rebuilt = features_for(pack, force=changed)
    status["steps"]["features_rebuilt"] = rebuilt
    elig, xok = eligibility(pack)
    # 7 shadow ledger (scores the chain signal sessions, settles closed periods)
    ledger = update_ledger(pack, feats, elig, xok, capital=a.capital)
    status["ledger"] = ledger["summary"]
    # 8 today's list if today is a chain signal day, or forced
    t = len(pack["dates"]) - 1
    is_signal_day = t in chain_signal_indices(pack["dates"], t)
    if is_signal_day or a.force_score:
        sig, _ = score_session(pack, feats, elig, xok, t, a.capital, tag="SIGNAL")
        status["signal"] = {"file": os.path.join(SIGNALS, "SIGNAL_%s.json" % pack["dates"][t]), "n_selected": sig["n_selected"], "is_chain_signal_day": is_signal_day}
    else:
        status["signal"] = {"is_chain_signal_day": False, "next_signal_date": ledger["summary"].get("next_signal_date")}
    status["elapsed_s"] = round(time.time() - t0, 1)
    status["orders_sent"] = False
    with open(STATUS, "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=1, ensure_ascii=False, default=str)
    print("ML1_LIVE DONE asof", asof_session, "ledger", ledger["summary"]["state"], "elapsed %.0fs" % status["elapsed_s"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
