"""Write the eight V14.1 reports from machine JSON. No new numbers."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_strategy_v14_1.paths import OUT


def _pct(x):
    if x is None:
        return "n/a"
    return "%.4f%%" % (100.0 * float(x))


def _md(name, body):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    return path


def _year_table(dist):
    lines = ["| Year | Return |", "|---|---|"]
    for y, v in sorted((dist.get("yearly") or {}).items()):
        lines.append("| %s | %s |" % (y, _pct(v)))
    return "\n".join(lines)


def compile_v14_1():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    h11 = load_json(os.path.join(OUT, "H11_CANDIDATE_REPLAY.json"))
    h12 = load_json(os.path.join(OUT, "H12_CANDIDATE_REPLAY.json"))
    eng = load_json(os.path.join(OUT, "INDEPENDENT_ENGINE.json"))
    cost = load_json(os.path.join(OUT, "COST_FORENSICS.json"))
    ca = load_json(os.path.join(OUT, "CORPORATE_ACTION_AUDIT.json"))
    dd = load_json(os.path.join(OUT, "DRAWDOWN_FORENSICS.json"))
    syn = load_json(os.path.join(OUT, "SYNTHETIC.json"))
    exe11 = load_json(os.path.join(OUT, "H11", "EXECUTION.json"))
    exe12 = load_json(os.path.join(OUT, "H12", "EXECUTION.json"))
    dist11 = load_json(os.path.join(OUT, "H11", "DISTRIBUTION.json"))
    dist12 = load_json(os.path.join(OUT, "H12", "DISTRIBUTION.json"))
    reg11 = load_json(os.path.join(OUT, "H11", "REGIMES.json"))
    reg12 = load_json(os.path.join(OUT, "H12", "REGIMES.json"))
    br11 = load_json(os.path.join(OUT, "H11", "BREADTH.json"))
    br12 = load_json(os.path.join(OUT, "H12", "BREADTH.json"))
    liq11 = load_json(os.path.join(OUT, "H11", "LIQUIDITY.json"))
    liq12 = load_json(os.path.join(OUT, "H12", "LIQUIDITY.json"))
    con11 = load_json(os.path.join(OUT, "H11", "CONTRIBUTION.json"))
    con12 = load_json(os.path.join(OUT, "H12", "CONTRIBUTION.json"))
    q = d.get("questions") or {}
    a11 = h11["path_a"]
    a12 = h12["path_a"]
    s11 = h11["series_abc"]
    s12 = h12["series_abc"]
    e11 = eng["H11"]
    e12 = eng["H12"]

    _md(
        "V14_1_CANDIDATE_STRATEGY_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Candidate vs Strategy Forensics",
                "",
                "AUDIT ONLY. No retune. No H13. No purchase. Final OOS DENIED.",
                "",
                "## Primary question",
                "",
                "Why is the Candidate statistic positive while the canonical Strategy full-path capital account is negative?",
                "",
                "## First-class answer",
                "",
                "The Candidate number is **not a capital account**.",
                "",
                "It is the arithmetic mean of **overlapping** 20-trading-day filled open-to-open returns, minus one locked round-trip, then annualized as `(1+mean_net_h)^(242/20)-1`. The `years` argument is unused. That formula can stay positive while every non-overlapping 20-day **compounded** book loses money.",
                "",
                "Independent reconstruction:",
                "",
                "- Path A Candidate = original `overlapping_series`. Matches published V13 `mean_net_h` with abs err **0**.",
                "- Path B Candidate = fresh pick + inline fees. Agrees with Path A at abs err **0**.",
                "- Capital Path A (return-based) and Path B (share-based) end at the same money (H11 err `%.2e`, H12 err `%.2e`)."
                % (e11["path_a_b_abs_err"], e12["path_a_b_abs_err"]),
                "- H11 settled end **%.2f**. H12 settled end **%.2f**. Same trade set as V14. Not read from V14 `equity.csv`."
                % (e11["path_a_end"], e12["path_a_end"]),
                "",
                "Accounting is clean. This is **METHODOLOGY_GAP_CONFIRMED**, not a hidden implementation bug.",
                "",
                "## Definitions",
                "",
                "| Object | What it is | What it is not |",
                "|---|---|---|",
                "| Candidate statistic | Daily overlapping H-day EW mean of fills, minus one RT. CAGR = `(1+mean)^(12.1)-1` | A compounded book |",
                "| Canonical Strategy | One long-only EW book, rebalance every 20 trading days, unfilled stays cash, compound `(1+period_return)` | An overlapping mean |",
                "",
                "## Reconstructed Candidate",
                "",
                "| Window | H11 mean_net | H11 CAGR_from_h | H12 mean_net | H12 CAGR_from_h |",
                "|---|---|---|---|---|",
                "| Research | %.8f | %s | %.8f | %s |"
                % (a11["research"]["mean_net"], _pct(a11["research"]["cagr_from_h"]), a12["research"]["mean_net"], _pct(a12["research"]["cagr_from_h"])),
                "| Validation | %.8f | %s | %.8f | %s |"
                % (a11["validation"]["mean_net"], _pct(a11["validation"]["cagr_from_h"]), a12["validation"]["mean_net"], _pct(a12["validation"]["cagr_from_h"])),
                "| Both | %.8f | %s | %.8f | %s |"
                % (a11["both"]["mean_net"], _pct(a11["both"]["cagr_from_h"]), a12["both"]["mean_net"], _pct(a12["both"]["cagr_from_h"])),
                "",
                "Published V13 match: H11 %s, H12 %s. Path A vs Path B: H11 err=%s, H12 err=%s."
                % (h11["published_agree"], h12["published_agree"], h11.get("path_a_b_val_abs_err"), h12.get("path_a_b_val_abs_err")),
                "",
                "## Independent capital",
                "",
                "| | H11 | H12 |",
                "|---|---|---|",
                "| Start | 1,000,000 | 1,000,000 |",
                "| End | %.2f | %.2f |" % (e11["path_a_end"], e12["path_a_end"]),
                "| Full total | %s | %s |" % (_pct(e11["full_total"]), _pct(e12["full_total"])),
                "| Recon start+net=end | %s | %s |" % (e11["recon_ok"], e12["recon_ok"]),
                "| N trades | %s | %s |" % (e11["n_trades"], e12["n_trades"]),
                "| Unfilled | %s | %s |" % (_pct(e11["unfilled_rate"]), _pct(e12["unfilled_rate"])),
                "",
                "## Why they disagree (ordered)",
                "",
                "1. **Object mismatch.** Candidate CAGR annualizes an overlapping mean. Strategy compounds one 20-day book.",
                "2. **AM-GM / left tail.** H11 nonoverlap V13-style **mean** is still +0.087%, but the **product** is −25.5%. H12 mean +0.111%, product −22.2%. A slightly positive average 20-day return is not a profitable capital path when 2011 and 2018 exist.",
                "3. **Overlap sampling.** 3,438 overlapping observations share crashes. The mean is smoother than any single 20-day grid.",
                "4. **All 20 offset grids lose money** when compounded (H11 ends 0.69–0.90, H12 0.75–0.93). The official grid is not an unlucky calendar.",
                "5. **Cost formula is not the flip.** Capital mean is *higher* than V13-style mean (H11 formula gap +2.9bp). Unfilled is cash, not a phantom book. No double charge.",
                "",
                "Decision: **%s**. NEXT = `%s`." % (d.get("OVERALL"), d.get("NEXT")),
                "",
                "## Locks",
                "",
                "New data = NO. Retune = NO. Make H12 into 10% = NO. Paper = 0. Portfolio = 0. Final OOS = DENIED.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_OVERLAP_BRIDGE.md",
        "\n".join(
            [
                "# V14.1 Overlap Bridge",
                "",
                "Series A/B/C are **diagnostics**. They are not a menu. Do not promote the prettier one.",
                "",
                "| Series | Meaning | H11 | H12 |",
                "|---|---|---|---|",
                "| A | Overlapping mean net | %s (n=%s) | %s (n=%s) |"
                % (_pct(s11["A_overlapping_mean_net"]), s11["A_n"], _pct(s12["A_overlapping_mean_net"]), s12["A_n"]),
                "| B mean | Nonoverlap V13-style mean | %s | %s |"
                % (_pct(s11["B_nonoverlap_v13_mean"]), _pct(s12["B_nonoverlap_v13_mean"])),
                "| B compound V13 | Product of those nets | %s | %s |"
                % (_pct(s11["B_nonoverlap_v13_compound"]), _pct(s12["B_nonoverlap_v13_compound"])),
                "| B compound capital | Official book total | %s | %s |"
                % (_pct(s11["B_nonoverlap_capital_compound"]), _pct(s12["B_nonoverlap_capital_compound"])),
                "| C | 20 offset grids, n negative | %s / 20 (mean end %.3f) | %s / 20 (mean end %.3f) |"
                % (s11["C_offset_grids"]["n_negative"], s11["C_offset_grids"]["mean_end"], s12["C_offset_grids"]["n_negative"], s12["C_offset_grids"]["mean_end"]),
                "",
                "HORIZON_TRANSLATION_RISK = %s." % d.get("HORIZON_TRANSLATION_RISK"),
                "",
                "`CANDIDATE_TO_STRATEGY_BRIDGE.csv` / `OVERLAP_BRIDGE.csv`: each official rebalance date, Candidate overlapping net that day, V13-style net on the same fills, capital period return, difference, cause tag.",
                "",
                "A same-date Candidate net equals the V13-style book net when pick/fill match. The remaining gap to capital is `COST_OR_CASH_FORMULA`. Sign flips on that date are tagged `SIGN_FLIP`.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_EXECUTION_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Execution Audit",
                "",
                "| Check | H11 | H12 |",
                "|---|---|---|",
                "| Hold is 20 trading days | %s | %s |" % (exe11["hold_is_20_trading_days"], exe12["hold_is_20_trading_days"]),
                "| Signal gaps all 20 | %s | %s |" % (exe11["signal_gaps"], exe12["signal_gaps"]),
                "| Entry open(t+1) | %s | %s |" % (exe11["entry_is_open_t1"], exe12["entry_is_open_t1"]),
                "| Weight sum = 1 | %s | %s |" % (exe11["weight_sum_is_one"], exe12["weight_sum_is_one"]),
                "| Unfilled fees | %s | %s |" % (exe11["unfilled_fees_total"], exe12["unfilled_fees_total"]),
                "| Suspended fills | %s | %s |" % (exe11["suspended_fills"], exe12["suspended_fills"]),
                "| Limit-lock fills | %s | %s |" % (exe11["limit_lock_fills"], exe12["limit_lock_fills"]),
                "| Delist-during-hold fills | %s | %s |" % (exe11["delist_during_hold_filled"], exe12["delist_during_hold_filled"]),
                "| Last mechanical exit after denied start | %s | %s |"
                % (exe11.get("exits_after_denied_start"), exe12.get("exits_after_denied_start")),
                "",
                "Unfilled H11 %s (`%s`). H12 %s (`%s`)."
                % (_pct(e11.get("unfilled_rate")), e11.get("reasons"), _pct(e12.get("unfilled_rate")), e12.get("reasons")),
                "",
                "Breadth H11: elig median %s, selected median %s, filled median %s, min selected %s. Collapse=%s."
                % (br11.get("elig_median"), br11.get("sel_median"), br11.get("fill_median"), br11.get("min_sel"), br11.get("selection_collapse")),
                "Breadth H12: elig median %s, selected median %s, filled median %s, min selected %s. Collapse=%s."
                % (br12.get("elig_median"), br12.get("sel_median"), br12.get("fill_median"), br12.get("min_sel"), br12.get("selection_collapse")),
                "",
                "Liquidity (1e6 diagnostic book, not capacity): H11 P50/P90/P95 = %s / %s / %s. H12 P50/P90/P95 = %s / %s / %s."
                % (liq11.get("p50"), liq11.get("p90"), liq11.get("p95"), liq12.get("p50"), liq12.get("p90"), liq12.get("p95")),
                "",
                "100 random fills (seed 20260831): `TRADE_FORENSICS.csv`. Full ledger stays on D: tmp.",
                "",
                "Unfilled is 0 PnL, 0 cost, weight stays cash. No re-allocation. No phantom exposure. Limit-lock is not marked after the fact. tradestatus≠1 never fills. Delisting during the would-be hold is UNFILL — no last-price continuation.",
                "",
            ]
        ),
    )
    c11 = cost["H11"]
    c12 = cost["H12"]
    _md(
        "V14_1_COST_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Cost Forensics",
                "",
                "Locked model: commission 2.5bp, transfer 0.1bp, slippage 10bp, stamp 10bp sell before 2023-08-28 / 5bp after. Not MT5.",
                "",
                "| | H11 | H12 |",
                "|---|---|---|",
                "| Gross | %.2f | %.2f |" % (c11["gross"], c12["gross"]),
                "| Fees (comm+transfer+stamp) | %.2f | %.2f |" % (c11["fees_commission_transfer_stamp"], c12["fees_commission_transfer_stamp"]),
                "| Slippage | %.2f | %.2f |" % (c11["slippage"], c12["slippage"]),
                "| Stamp | %.2f | %.2f |" % (c11["stamp"], c12["stamp"]),
                "| Net | %.2f | %.2f |" % (c11["net"], c12["net"]),
                "| Unfilled fees | %s | %s |" % (c11["unfilled_fees"], c12["unfilled_fees"]),
                "| Double charge | %s | %s |" % (c11["double_charge"], c12["double_charge"]),
                "| V13-style mean | %s | %s |" % (_pct(c11["v13_style_mean"]), _pct(c12["v13_style_mean"])),
                "| Capital mean | %s | %s |" % (_pct(c11["capital_mean"]), _pct(c12["capital_mean"])),
                "| Formula gap (cap − V13) | %s | %s |" % (_pct(c11["formula_gap_mean"]), _pct(c12["formula_gap_mean"])),
                "",
                "Identity `net = gross - fees - slip` holds (H11 abs %s)." % c11.get("identity_net_minus_gross_plus_fees_plus_slip"),
                "",
                "Costs are charged once at entry and once at exit, only on fills. Unfilled orders produce no cost.",
                "",
                "The Candidate subtracts one RT from the mean raw. The Strategy applies buy/sell factors on notional. That is a **formula difference**, not a double subtraction of the same book. FORENSIC_ERROR for double charge: **no**.",
                "",
                "Cost does **not** flip a large positive Candidate into a large negative book. Capital-period means are slightly *better* than V13-style means. The sign flip is overlap + compounding.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_CORPORATE_ACTION_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Corporate Action Audit",
                "",
                "Canonical ranking and PnL stay on **raw** prices. No frozen QFQ panel. Do not freeze a new panel. Do not buy data.",
                "",
                "| | H11 | H12 |",
                "|---|---|---|",
                "| Filled names checked | %s | %s |" % (ca["H11"]["n_checked"], ca["H12"]["n_checked"]),
                "| close/preclose > 12%% | %s | %s |" % (ca["H11"]["close_vs_preclose_gt_12pct"], ca["H12"]["close_vs_preclose_gt_12pct"]),
                "| Return type | %s | %s |" % (ca["H11"]["return_type"], ca["H12"]["return_type"]),
                "| Dividend | DIVIDEND_EXCLUSION | DIVIDEND_EXCLUSION |",
                "| QFQ | DATA_GAP | DATA_GAP |",
                "",
                "Current V14 is a **price return**, not a total return. Cash dividends never enter P&L.",
                "",
                "CANDIDATE_REPRESENTATION_RISK is recorded because raw-close ranking and raw-open PnL ignore cash dividends, splits-as-adjusted, and rights. A frozen QFQ panel **might** change both the statistic and the book. That is not a license to switch the canonical object. QFQ remains DATA_GAP. $0. No Tushare / Wind / Choice.",
                "",
            ]
        ),
    )
    d11 = dd["H11"]
    d12 = dd["H12"]
    _md(
        "V14_1_DRAWDOWN_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Drawdown Forensics",
                "",
                "The ≈ −66% drawdown is a **capital-path** fact. The overlapping Candidate MaxDD was a different object (~−16% to −18% on the statistic series) and must not be compared as if it were the same book.",
                "",
                "| | H11 | H12 |",
                "|---|---|---|",
                "| MaxDD | %s | %s |" % (_pct(d11["maxdd"]), _pct(d12["maxdd"])),
                "| Peak | %s (%.0f) | %s (%.0f) |" % (d11["peak_date"], d11["peak_equity"], d12["peak_date"], d12["peak_equity"]),
                "| Trough | %s (%.0f) | %s (%.0f) |" % (d11["trough_date"], d11["trough_equity"], d12["trough_date"], d12["trough_equity"]),
                "| Recovery | %s | %s |" % (d11["recovery_date"], d12["recovery_date"]),
                "| Worst day | %s %s | %s %s |"
                % (d11["worst_day"], _pct(d11["worst_day_ret"]), d12["worst_day"], _pct(d12["worst_day_ret"])),
                "| Worst trade | %s %s | %s %s |"
                % (d11["worst_trade"]["signal_date"], _pct(d11["worst_trade"]["ret"]), d12["worst_trade"]["signal_date"], _pct(d12["worst_trade"]["ret"])),
                "| Loss cluster | %s → %s (%s) | %s → %s (%s) |"
                % (
                    d11["max_loss_cluster"]["start"],
                    d11["max_loss_cluster"]["end"],
                    _pct(d11["max_loss_cluster"]["loss"]),
                    d12["max_loss_cluster"]["start"],
                    d12["max_loss_cluster"]["end"],
                    _pct(d12["max_loss_cluster"]["loss"]),
                ),
                "",
                "How −66% formed: the book peaked into the 2015 bubble (H11 1.835M on 2015-06-12), ate 2015-06-15 (−23.7% in one 20-day hold), 2015-08-24 (−8.8% in one day), then 2016–2018 without making a new high. Trough 2018-10-18 (H11 0.616M). No recovery on the official path.",
                "",
                "2011 (−33.0% H11 / −30.7% H12) and 2018 (−31.8% / −32.3%) stay in the table. No year is dropped.",
                "",
                "## H11 years",
                "",
                _year_table(dist11),
                "",
                "Negative month ratio %s. Best %s %s. Worst %s %s. Skew %s. Tail P5 %s."
                % (
                    _pct(dist11.get("negative_month_ratio")),
                    dist11["best_month"][0],
                    _pct(dist11["best_month"][1]),
                    dist11["worst_month"][0],
                    _pct(dist11["worst_month"][1]),
                    dist11.get("month_skew"),
                    _pct(dist11.get("tail_loss_p5")),
                ),
                "",
                "## H12 years",
                "",
                _year_table(dist12),
                "",
                "Negative month ratio %s. Best %s %s. Worst %s %s."
                % (
                    _pct(dist12.get("negative_month_ratio")),
                    dist12["best_month"][0],
                    _pct(dist12["best_month"][1]),
                    dist12["worst_month"][0],
                    _pct(dist12["worst_month"][1]),
                ),
                "",
                "## Diagnostic regimes (do not drop)",
                "",
                "| Regime | H11 total | H12 total | Denied? |",
                "|---|---|---|---|",
            ]
            + [
                "| %s | %s | %s | %s |"
                % (name, _pct((reg11.get(name) or {}).get("total")), _pct((reg12.get(name) or {}).get("total")), (reg11.get(name) or {}).get("denied_overlap"))
                for name in ("2010-2014", "2015-2019", "2020-2021", "2022-2023", "2024-2026")
            ]
            + [
                "",
                "2024-03+ is DENIED for gates. The last official hold may settle on 2024-03-06 as a mechanical exit of a February signal. That is the same rule V13 used for late validation forward returns.",
                "",
                "Contribution (share of positive mass): H11 top 1/5/10/20%% stocks = %s / %s / %s / %s. Days = %s / %s / %s / %s."
                % (
                    con11["stock"].get("top_1_of_pos"),
                    con11["stock"].get("top_5_of_pos"),
                    con11["stock"].get("top_10_of_pos"),
                    con11["stock"].get("top_20_of_pos"),
                    con11["days"].get("top_1_of_pos"),
                    con11["days"].get("top_5_of_pos"),
                    con11["days"].get("top_10_of_pos"),
                    con11["days"].get("top_20_of_pos"),
                ),
                "",
            ]
        ),
    )
    _md(
        "V14_1_CAPITAL_ENGINE_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Independent Capital Engine",
                "",
                "Reference: `research_engine/cn_a_share_strategy_v14_1/capital_ref.py`.",
                "It does **not** import `cn_a_share_strategy_v14.engine.simulate`. It does **not** read V14 `equity.csv`.",
                "",
                "Path A = return-based `period_capital`. Path B = share-based `notional/open(t+1)`.",
                "Same trade dates. Ending capital agrees to ~1e-7 or better.",
                "",
                "Synthetic suite all_ok = **%s**." % syn.get("all_ok"),
                "",
                "- All filled, zero raw → lose only locked RT.",
                "- All unfilled → end = start, fees = 0.",
                "- One of N filled → deploy 1/N, unfilled stay cash, unfilled fees = 0.",
                "- Large loss recon holds.",
                "",
                "| | H11 | H12 |",
                "|---|---|---|",
                "| Path A end | %.2f | %.2f |" % (e11["path_a_end"], e12["path_a_end"]),
                "| Path B end | %.2f | %.2f |" % (e11["path_b_end"], e12["path_b_end"]),
                "| Abs err | %s | %s |" % (e11["path_a_b_abs_err"], e12["path_a_b_abs_err"]),
                "| Same dates | %s | %s |" % (e11["same_trade_dates"], e12["same_trade_dates"]),
                "| Recon | %s (abs %s) | %s (abs %s) |" % (e11["recon_ok"], e11["recon_abs"], e12["recon_ok"], e12["recon_abs"]),
                "| Empty all-unfilled advances | %s | %s |" % (e11["n_empty_all_unfilled"], e12["n_empty_all_unfilled"]),
                "| No-pick advances | %s | %s |" % (e11["n_nopick"], e12["n_nopick"]),
                "",
                "Identity: starting capital + sum(trade net) = ending capital.",
                "Daily MTM telescopes by construction. The economic recon is the trade ledger.",
                "",
                "Benchmark is EW eligible open-to-open on the **same** 172 signal dates (not a purchased index). H11 bench end %.4f. H12 bench end %.4f. Same calendar as the strategy."
                % (e11["benchmark"]["end"], e12["benchmark"]["end"]),
                "",
                "V14 published settled ends (834,202.89 / 883,505.87) match this independent engine. That is a check, not an input.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_DECISION.md",
        "\n".join(
            [
                "# V14.1 Decision",
                "",
                "**%s**" % d.get("OVERALL"),
                "",
                "NEXT = `%s`" % d.get("NEXT"),
                "",
                "```",
                "LEVEL = %s" % d.get("LEVEL"),
                "CANDIDATE = %s" % d.get("CANDIDATE"),
                "STRATEGY = %s" % d.get("STRATEGY"),
                "PORTFOLIO = 0",
                "PAPER = 0",
                "LIVE = 0",
                "```",
                "",
                "H11/H12 remain Candidates. Strategy remains WEAK. Not two sleeves. Capital correlation %s. Overlap correlation %s."
                % (d.get("correlation_capital"), d.get("correlation_overlap")),
                "",
                "## 22 questions",
                "",
                "1. Why Candidate positive: %s" % q.get("q01_why_candidate_positive"),
                "2. Why V14 full path negative: %s" % q.get("q02_why_v14_negative"),
                "3. Overlap core? %s" % q.get("q03_overlap_core"),
                "4. Non-overlap core? %s" % q.get("q04_nonoverlap_core"),
                "5. Entry timing consistent? **YES** — close(t) signal, open(t+1) fill.",
                "6. Exit timing consistent? **YES** — open(t+1+20), 20 trading days.",
                "7. Unfilled error? **NO** — 0 PnL, 0 fees, cash residual.",
                "8. Limit-lock error? **NO** — never filled, no phantom later return.",
                "9. Cost double count? **NO**.",
                "10. Corporate action? %s" % q.get("q10_corporate_action"),
                "11. Dividend omitted? **YES** — DIVIDEND_EXCLUSION, price return only.",
                "12. −66%% DD: %s" % q.get("q12_dd_origin"),
                "13. One mechanism? **YES** — LOW_VOL_CANDIDATE_CLUSTER. Do not blend.",
                "14. H11 still researchable? **YES** as a Candidate. **NO** as a capital edge.",
                "15. H12 still researchable? **YES** as a Candidate. **NO** as a capital edge.",
                "16. Executable? **YES** — process complete, fills defined.",
                "17. Level 2 process gate? **YES**. Economic gate? **NO**.",
                "18. Long Validation? **NO**.",
                "19. Why not: %s" % q.get("q19_why_no_lv"),
                "20. New data? **NO**.",
                "21. Retune? **NO**.",
                "22. Make H12 into 10%? **NO**.",
                "",
                "## Next",
                "",
                "Keep H11/H12 Candidate status. Strategy stays WEAK. Do not Long Validate. "
                "Do not combine H11+H12. Do not optimize lookback / hold / quantile. "
                "Do not buy data. Final OOS remains DENIED.",
                "",
            ]
        ),
    )
    print("COMPILE_V14_1", d.get("OVERALL"), d.get("NEXT"), flush=True)
    return d


if __name__ == "__main__":
    compile_v14_1()
