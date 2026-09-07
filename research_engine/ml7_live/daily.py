"""ML7 daily forward step (output-only). Called by ml1_live.daily after ML1 has written its files, or standalone:

    python -m research_engine.ml7_live.daily [--asof YYYY-MM-DD] [--skip-fetch] [--force-score]

Never changes SIGNAL / SHORTLIST / LEDGER / LEDGER_TOP20. Never sends orders. Never writes into frozen research dirs.
"""
from __future__ import print_function

import argparse
import datetime
import json
import os
import sys
import time

from research_engine.ml7_live import STATUS, set_env

TAG = "ML7_LIVE"


def run(pack, elig, xok, asof_session, skip_fetch=False, force_score=False, capital=None, ml1_scores=None, ml1_today_scores=None):
    """pack/elig/xok = the live pack ML1 just used (same sessions, same eligibility). Returns a status dict."""
    from research_engine.ml1_live import DEFAULT_CAPITAL
    from research_engine.ml1_live.ledger import chain_signal_indices

    set_env(asof_session)
    from research_engine.ml7_live import refresh
    from research_engine.ml7_live.features import build_all
    from research_engine.ml7_live.ledger import update_ledger
    from research_engine.ml7_live.score import score_session

    t0 = time.time()
    capital = capital or DEFAULT_CAPITAL
    st = {"asof_session": asof_session, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "steps": {}}
    st["steps"]["refresh"] = "skipped" if skip_fetch else refresh.refresh_all(asof_session)
    feats, rebuilt = build_all(pack, elig, force=not skip_fetch)
    st["steps"]["features_rebuilt"] = rebuilt
    led = update_ledger(pack, feats, elig, xok, capital=capital, ml1_scores=ml1_scores)
    st["ledger"] = led["summary"]
    t = len(pack["dates"]) - 1
    if t in chain_signal_indices(pack["dates"], t) or force_score:
        sig, _ = score_session(pack, feats, elig, xok, t, capital, tag="SIGNAL_ML7")
        st["signal"] = {"signal_date": pack["dates"][t], "n_selected": sig["n_selected"], "model_refit_date": sig["model_refit_date"]}
    st["elapsed_s"] = round(time.time() - t0, 1)
    st["orders_sent"] = False
    st["affects_shortlist"] = False
    with open(STATUS, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, default=str)
    print(TAG, "DONE asof", asof_session, "ledger", st["ledger"].get("state"), "elapsed %.0fs" % st["elapsed_s"], flush=True)
    return st


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=datetime.date.today().isoformat())
    ap.add_argument("--skip-fetch", action="store_true")
    ap.add_argument("--force-score", action="store_true")
    a = ap.parse_args(argv)
    # reuse ML1's live pack exactly as daily.py builds it (no refetch here; ML1's daily is the fetcher)
    from research_engine.ml1_live import daily as ml1_daily
    from research_engine.ml1_live import panel
    from research_engine.ml1_live.score import eligibility

    ml1_daily._set_env(a.asof)
    equities = panel.load_live_equities()
    cal = panel.load_live_calendar()
    days = panel.trading_days(cal)
    asof_session = max(d for d in days if d <= a.asof)
    live_sessions = [d for d in days if d > panel.FROZEN_END]
    pack = panel.build_live_pack(equities, live_sessions, asof_session)
    elig, xok = eligibility(pack)
    run(pack, elig, xok, asof_session, skip_fetch=a.skip_fetch, force_score=a.force_score)
    return 0


if __name__ == "__main__":
    sys.exit(main())
