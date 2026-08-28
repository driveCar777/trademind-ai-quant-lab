"""Render Recovery markdown. Facts only."""
from __future__ import print_function


def _pct_line(coverage):
    lines = []
    order = (
        "direction",
        "relative_value",
        "state_transition",
        "risk_premium",
        "event",
        "microstructure",
        "time_institutional",
        "volatility_realized",
    )
    for key in order:
        row = coverage.get(key) or {}
        lines.append(
            "- %s: covered %s%% (%s/%s slots)"
            % (key, row.get("covered_pct"), row.get("n_covered"), row.get("n_slots"))
        )
    return lines


def render_recovery_report(gap, coverage, selection, calendar, capability):
    families = gap.get("families") or []
    chosen = (selection.get("chosen_row") or {})
    lines = [
        "# Alpha Recovery Report V1.0",
        "",
        "Not a strategy. Not a 10% CAGR claim. Level is still **0**. Candidate = **0**.",
        "",
        "Frozen families were **read**, not rewritten: HYP-0001, FD V0.1, V0.5, V0.6, V0.8, V0.9, V0.91.",
        "",
        "Final OOS: **DENIED**.",
        "",
        "## 1. Covered probability space",
        "",
    ]
    lines.extend(_pct_line(coverage))
    lines.extend(
        [
            "",
            "Direction and state-level price rules were exhausted. Relative-value was tested twice (V0.8 wrong object, V0.91 residual). Risk premium, scheduled events, and institutional time were not contracted. Microstructure was tested only as next-return *level* (FD tickvol_z), not as surprise/divergence.",
            "",
            "## 2. Information-gap codes (A-E)",
            "",
            "| family | codes | outcome | why |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in families:
        why = "; ".join(row.get("why") or [])
        lines.append(
            "| %s | %s | %s | %s |"
            % (row.get("family"), ",".join(row.get("codes") or []), row.get("outcome"), why)
        )
    lines.extend(
        [
            "",
            "Code key: **A** no usable predictive information; **B** fragment eaten by cost; **C** wrong timescale; **D** missing data; **E** wrong expression of a nearby idea.",
            "",
            "Dominant code: **%s**." % gap.get("dominant_code"),
            "",
            "## 3. Why the existing search space produced no alpha",
            "",
            gap.get("search_space_why_empty") or "",
            "",
            "## 4. Remaining unknown space that still has data",
            "",
            "- Institutional month-end / month-start on frozen D1 (never contracted).",
            "- Realized-vol term structure and volume-return divergence (OHLC + tick_volume on disk).",
            "- London/NY open: economically real. Frozen H1 is months; broker probe meets ~5.03y as **new IDs only**.",
            "- IV / carry / news: still **D / BLOCKED**.",
            "",
            "## 5. Calendar occupancy on frozen D1 (dates only)",
            "",
        ]
    )
    for row in calendar or []:
        lines.append(
            "- %s n=%s month_end=%s month_start=%s quarter_end=%s RESEARCH_ME~%s VAL_ME~%s"
            % (
                row.get("asset"),
                row.get("n_dates"),
                row.get("n_month_end"),
                row.get("n_month_start"),
                row.get("n_quarter_end"),
                row.get("research_month_end_est"),
                row.get("validation_month_end_est"),
            )
        )
    lines.extend(
        [
            "",
            "hold=5 does not collide with monthly events. RESEARCH month-end count is above the n_trade>=8 gate if the event fires.",
            "",
            "## 6. Selected family (one)",
            "",
            "- **%s** - %s" % (selection.get("chosen"), chosen.get("mechanism_text")),
            "- why not tested before: %s" % (selection.get("why") or chosen.get("why_not_tested")),
            "- score: %s" % chosen.get("score"),
            "",
            "Contract: `INSTITUTIONAL_TIME_V1.0`. **Not executed.**",
            "",
        ]
    )
    return "\n".join(lines)


def render_data_md(cap):
    lines = [
        "# DATA_CAPABILITY_REAL V1",
        "",
        "Do not assume. On-disk packs and a read-only MT5 probe.",
        "",
        "Recovery targets: **D1 > 10 years**, **H1 > 5 years**, **M15 > 2 years**.",
        "",
        "Overall: **%s**" % cap.get("overall"),
        "",
        "Final OOS: **DENIED**. No `order_send`. No overwrite of `*-20260825-000001`.",
        "",
        "## Targets vs probe",
        "",
    ]
    verdict = cap.get("verdict") or {}
    for tf in ("D1", "H1", "M15"):
        row = verdict.get(tf) or {}
        lines.append(
            "- **%s** target=%sy meet=%s short=%s blocked=%s meet_assets=%s short_assets=%s"
            % (
                tf,
                row.get("target_years"),
                row.get("n_meets"),
                row.get("n_shortfall"),
                row.get("n_blocked"),
                ",".join(row.get("assets_meet") or []) or "-",
                ",".join(row.get("assets_short") or []) or "-",
            )
        )
    lines.extend(["", "## On-disk immutable (do not rewrite)", ""])
    for row in cap.get("disk") or []:
        if row.get("timeframe") not in ("D1", "H1", "M15"):
            continue
        lines.append(
            "- %s %s years=%.2f n=%s target=%s **%s** `%s`"
            % (
                row.get("asset"),
                row.get("timeframe"),
                row.get("years") or 0.0,
                row.get("n"),
                row.get("target_years"),
                row.get("coverage"),
                row.get("dataset_id"),
            )
        )
    lines.extend(["", "## Read-only MT5 probe", ""])
    for row in cap.get("probe_rows") or []:
        span = row.get("span_years")
        span_s = "-" if span is None else "%.3f" % span
        lines.append(
            "- %s %s n=%s span_years=%s first_unix=%s **%s**"
            % (
                row.get("asset"),
                row.get("timeframe"),
                row.get("n"),
                span_s,
                row.get("first_unix"),
                row.get("coverage") or row.get("status"),
            )
        )
    if not (cap.get("probe_rows") or []):
        lines.append("- probe status: %s %s" % ((cap.get("probe") or {}).get("status"), (cap.get("probe") or {}).get("reason") or ""))
    lines.extend(["", "## Phase 7 acquisition (honest)", ""])
    acq = cap.get("acquisition") or {}
    lines.append(acq.get("note") or "")
    lines.append("")
    for item in acq.get("items") or []:
        lines.extend(
            [
                "### %s - priority %s - %s" % (item.get("id"), item.get("priority"), item.get("status")),
                "",
                "- need: %s" % item.get("need"),
                "- why: %s" % item.get("why"),
                "- cost: %s" % item.get("cost"),
                "- action: %s" % item.get("action"),
                "",
            ]
        )
    lines.extend(
        [
            "## Rules",
            "",
            "1. New `dataset_id` only.",
            "2. Never overwrite `20260825-000001`.",
            "3. If first unix does not move, history does not exist. Record BLOCKED.",
            "4. Do not invent IV / news / roll tape.",
            "",
        ]
    )
    return "\n".join(lines)


def render_decision_md(selection, space, calendar, capability):
    chosen = selection.get("chosen_row") or {}
    lines = [
        "# NEXT_ALPHA_DECISION",
        "",
        "One family. Paper contract only. **Do not run.**",
        "",
        "## Decision",
        "",
        "- selected: **%s**" % selection.get("chosen"),
        "- family: `INSTITUTIONAL_TIME_V1.0` / `FAM-IT-CALENDAR-0001`",
        "- search_space_hash: `%s`" % ((space or {}).get("search_space_hash")),
        "- executed: **false**",
        "",
        "## Why this one",
        "",
        "- previously **UNKNOWN** (no calendar contract exists).",
        "- data **available**: frozen GOLD/OIL D1 timestamps.",
        "- economic mechanism: month-end / month-start institutional rebalance, not an indicator.",
        "- not RSI / MACD / MA / breakout.",
        "- not V0.8 isomorph. not V0.9 retune. not V0.91 SMA60.",
        "",
        "## Why not the others",
        "",
        "- London/NY open: frozen H1 is months. Broker probe meets ~5.03y as new IDs. Not selected: data is not on the immutable packs.",
        "- RV term structure / vol-of-vol: adjacent to V0.9 VOL_SHOCK (isomorph risk).",
        "- volume surprise/divergence: FD already killed tickvol as next-return *level*; still UNKNOWN but lower cost-survival score.",
        "- USD proxy / basket residual: FAILED isomorphs.",
        "- IV / carry: DATA_BLOCKED.",
        "- weekday: FORBIDDEN.",
        "",
        "## Why not tested before",
        "",
        chosen.get("why_not_tested") or "",
        "",
        "## TOP 10 (Opportunity V2)",
        "",
        "| rank | id | score | status | why not tested |",
        "| --- | --- | --- | --- | --- |",
    ]
    for i, row in enumerate(selection.get("top10") or [], 1):
        lines.append(
            "| %s | %s | %s | %s | %s |"
            % (i, row.get("id"), row.get("score"), row.get("status"), row.get("why_not_tested"))
        )
    lines.extend(["", "## Calendar counts (frozen D1 dates)", ""])
    for row in calendar or []:
        lines.append(
            "- %s month_end=%s month_start=%s quarter_end=%s"
            % (row.get("asset"), row.get("n_month_end"), row.get("n_month_start"), row.get("n_quarter_end"))
        )
    lines.extend(
        [
            "",
            "## Contract (locked, not run)",
            "",
            "- hypotheses: HYP-IT-0001 GOLD month-end +; HYP-IT-0002 OIL month-end +; HYP-IT-0003 GOLD month-start +",
            "- hold=5, NEXT_BAR_OPEN, V0.6 cost, seed 20260825, FDR m=3, 70/15/15, Final OOS DENIED",
            "- failure: do not widen the event window after seeing PnL; INSUFFICIENT_OCCUPANCY fails the ID",
            "- Level 1 still requires FDR + both targets after cost. This contract does not grant it.",
            "",
            "## Data gate",
            "",
            "- selected family: **does not wait** on acquisition.",
            "- Recovery H1 5y overall: **%s**" % (capability or {}).get("overall"),
            "",
            "Stop here. Wait for review.",
            "",
        ]
    )
    return "\n".join(lines)


def render_contract_md(space, calendar):
    lines = [
        "# INSTITUTIONAL_TIME_V1.0 Contract",
        "",
        "Locked. Design only. **Not executed. Not a runner. Not V0.8 / V0.9 / V0.91.**",
        "",
        "```text",
        "search_space_hash =",
        (space or {}).get("search_space_hash") or "",
        "```",
        "",
        "Do not run until reviewed. Do not add a fourth ID. Do not widen the window after PnL.",
        "",
        "## 0. Family",
        "",
        "| field | value |",
        "| --- | --- |",
        "| family_id | `FAM-IT-CALENDAR-0001` |",
        "| discovery_id | `INSTITUTIONAL_TIME_V1.0` |",
        "| status | `LOCKED_NOT_RUN` |",
        "| hypothesis_ids | `HYP-IT-0001` `HYP-IT-0002` `HYP-IT-0003` |",
        "| timeframe | D1 |",
        "| hold_bars | 5 |",
        "| seed | 20260825 |",
        "",
        "### Hypothesis",
        "",
        "Month-end and month-start are **institutional** events (benchmark rebalance, commodity-book flattening, new-month allocation), not weekday dummies and not indicator crosses.",
        "",
        "### Mechanism",
        "",
        "Because allocated books and dealers flatten or refill at calendar turns,",
        "when the last (or first) D1 bar of a calendar month is observed at t,",
        "the next 5 D1 bars of GOLD or OIL, filled at next open, after V0.6 costs,",
        "are predicted **positive**.",
        "",
        "### Not",
        "",
        "- weekday / weekend-gap fishing",
        "- RSI / MACD / MA combination / breakout parameter search",
        "- V0.8 next-day dollar proxy",
        "- V0.9 delta-state / VOL_SHOCK retune",
        "- V0.91 residual / SMA60",
        "- widening T-2..T+2 after seeing PnL",
        "",
        "## 1. Dataset",
        "",
        "Parents (immutable, do not rewrite):",
        "",
        "- `tm-market-GOLD-D1-20260825-000001`",
        "- `tm-market-OIL-D1-20260825-000001`",
        "",
        "Windows: 70/15/15 on **each target's own D1 dates**. Final OOS last 15% DENIED.",
        "",
        "## 2. Signal / target",
        "",
        "| ID | event | target | predicted_sign |",
        "| --- | --- | --- | --- |",
        "| HYP-IT-0001 | last D1 bar of calendar month | GOLD | +1 |",
        "| HYP-IT-0002 | last D1 bar of calendar month | OIL | +1 |",
        "| HYP-IT-0003 | first D1 bar of calendar month | GOLD | +1 |",
        "",
        "Feature uses only information <= t. Fill `NEXT_BAR_OPEN`. Close fill FORBIDDEN.",
        "Overlap skip if a new event fires inside an open 5-bar hold.",
        "",
        "## 3. Cost / evaluation",
        "",
        "Copy V0.6: half spread broker-points, commission 5 bp/side, slippage 10 bp/side,",
        "risk 0.5% equity, leverage <=1x, stop 1.5xATR or hold end.",
        "seed 20260825, bootstrap/perm 2000, block=5, FDR q=0.05 m=3.",
        "Gates: RESEARCH n_trade>=8, validation n_trade>=4, occupancy<=0.40,",
        "costed TR>0 and predicted sign on both RESEARCH and validation.",
        "Program CANDIDATE needs FDR and **both targets** after cost.",
        "CAGR>=10% is not a gate.",
        "",
        "## 4. Failure condition",
        "",
        "- INSUFFICIENT_OCCUPANCY / n_trade below gate → fail the ID. **Do not widen the window.**",
        "- Sign flip after seeing PnL → new discovery_id, not an amendment.",
        "- Adding weekday, RSI, or a fourth ID → contract breach.",
        "- Reading Final OOS → denied.",
        "",
        "## 5. Calendar counts used to justify the contract (dates only)",
        "",
    ]
    for row in calendar or []:
        lines.append(
            "- %s n=%s month_end=%s month_start=%s quarter_end=%s RESEARCH_ME~%s"
            % (
                row.get("asset"),
                row.get("n_dates"),
                row.get("n_month_end"),
                row.get("n_month_start"),
                row.get("n_quarter_end"),
                row.get("research_month_end_est"),
            )
        )
    lines.extend(
        [
            "",
            "## Canonical payload",
            "",
            "See `research_engine/opportunity/contract_it.py` `CANONICAL_PAYLOAD`.",
            "If any hashed field changes, it is not V1.0.",
            "",
            "## Untouched",
            "",
            "HYP-0001 14:11, FD, V0.5, V0.6, V0.8, V0.9, V0.91, immutable bars, Final OOS, MT5 orders.",
            "",
        ]
    )
    return "\n".join(lines)
