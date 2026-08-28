"""Read-only audit of frozen GOLD M15 RSI 14/30/80 ledger. Does not call Xavier."""
from __future__ import print_function

import json
import os

LEDGER = os.path.join(
    os.path.dirname(__file__), "..", "data", "mine", "longrun", "review_ledgers.json"
)
OUT = os.path.join(
    os.path.dirname(__file__), "..", "data", "mine", "longrun", "manual_review_gold_m15.json"
)
CUT = 1400


def pair_pnl(buy_px, sell_px):
    # Frozen worker formula in _rsi_bt: round((sp-ep)/ep*100, 2)
    return round((sell_px - buy_px) / buy_px * 100.0, 2)


def streaks(signs):
    max_w = max_l = cur_w = cur_l = 0
    for s in signs:
        if s > 0:
            cur_w += 1
            cur_l = 0
            max_w = max(max_w, cur_w)
        elif s < 0:
            cur_l += 1
            cur_w = 0
            max_l = max(max_l, cur_l)
        else:
            cur_w = cur_l = 0
    return max_w, max_l


def side_stats(pairs):
    pnls = [p["pnl_pct"] for p in pairs]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    zeros = [x for x in pnls if x == 0]
    gross_win = round(sum(wins), 2)
    gross_loss = round(sum(losses), 2)
    signs = [1 if x > 0 else (-1 if x < 0 else 0) for x in pnls]
    max_w, max_l = streaks(signs)
    ranked = sorted(pairs, key=lambda item: item["pnl_pct"], reverse=True)
    return {
        "complete_roundtrips": len(pairs),
        "win_n": len(wins),
        "loss_n": len(losses),
        "flat_n": len(zeros),
        "win_rate_on_sells_pct": round(100.0 * len(wins) / len(pairs), 1) if pairs else None,
        "sum_pair_pnl_pct": round(sum(pnls), 2),
        "gross_win_pct": gross_win,
        "gross_loss_pct": gross_loss,
        "avg_win_pct": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss_pct": round(sum(losses) / len(losses), 2) if losses else None,
        "max_win": ranked[0] if ranked else None,
        "max_loss": min(pairs, key=lambda item: item["pnl_pct"]) if pairs else None,
        "max_consecutive_wins": max_w,
        "max_consecutive_losses": max_l,
        "pair_pnl_sequence": pnls,
        "hold_bars": [p["hold_bars"] for p in pairs],
    }


def concentration(pairs):
    if not pairs:
        return None
    pnls = [p["pnl_pct"] for p in pairs]
    total = sum(pnls)
    wins = sorted([x for x in pnls if x > 0], reverse=True)
    gross_win = sum(wins) if wins else 0.0
    top1 = wins[0] if wins else 0.0
    top3 = sum(wins[:3])
    top5 = sum(wins[:5])
    without_top1 = round(total - top1, 2)
    without_top3 = round(total - top3, 2)
    return {
        "sum_pair_pnl_pct": round(total, 2),
        "gross_win_pct": round(gross_win, 2),
        "max_win_share_of_gross_win": round(top1 / gross_win, 4) if gross_win else None,
        "top3_share_of_gross_win": round(top3 / gross_win, 4) if gross_win else None,
        "top5_share_of_gross_win": round(top5 / gross_win, 4) if gross_win else None,
        "sum_after_drop_max_win": without_top1,
        "sum_after_drop_top3_wins": without_top3,
        "still_positive_after_drop_max_win": without_top1 > 0,
        "still_positive_after_drop_top3_wins": without_top3 > 0,
        "note": "pair pnl_pct uses frozen (sp-ep)/ep*100 on slipped prices. Not worker equity profit%. Commission not in pair pnl.",
    }


def main():
    raw = json.load(open(os.path.abspath(LEDGER), encoding="utf-8"))
    row = None
    for item in raw.get("ledgers") or []:
        if item.get("id") == "rsi-14-30-80":
            row = item
            break
    if not row:
        print("NO_LEDGER")
        return 1
    fills = row.get("fills") or []
    is_fills = [f for f in fills if int(f["idx"]) < CUT]
    oos_fills = [f for f in fills if int(f["idx"]) >= CUT]

    def pairs_of(events):
        out = []
        pending = None
        for ev in events:
            if ev.get("type") == "BUY":
                pending = ev
            elif ev.get("type") == "SELL" and pending:
                pnl = pair_pnl(float(pending["price"]), float(ev["price"]))
                out.append({
                    "buy_idx": int(pending["idx"]),
                    "sell_idx": int(ev["idx"]),
                    "buy_price": pending["price"],
                    "sell_price": ev["price"],
                    "hold_bars": int(ev["idx"]) - int(pending["idx"]),
                    "pnl_pct": pnl,
                })
                pending = None
        leftover = pending["idx"] if pending else None
        return out, leftover

    is_pairs, is_open = pairs_of(is_fills)
    oos_pairs, oos_open = pairs_of(oos_fills)
    all_pairs, all_open = pairs_of(fills)

    idxs = [int(f["idx"]) for f in fills]
    report = {
        "id": row.get("id"),
        "symbol": row.get("symbol"),
        "timeframe": row.get("timeframe"),
        "bars": row.get("bars"),
        "cut": row.get("cut"),
        "verdict": row.get("verdict"),
        "frozen_is": row.get("is"),
        "frozen_oos": row.get("oos"),
        "is_score": row.get("is_score"),
        "fill_n": row.get("fill_n"),
        "definition": {
            "fill": "one trades[] event from worker: BUY or SELL (SPEC 24.4 type/idx/price; SELL also has pnl_pct in worker, stripped in this ledger file)",
            "total_trades_is_oos": "len(fills in segment) after _attach_cut split by idx vs cut; same as _segment total_trades",
            "full_window_total_trades": "len(trades) in _std_metrics = BUY+SELL count",
            "why_38_and_26_12": "38 full-window events; 26 with idx<1400; 12 with idx>=1400",
        },
        "is_fill_counts": {
            "n": len(is_fills),
            "buy": sum(1 for f in is_fills if f["type"] == "BUY"),
            "sell": sum(1 for f in is_fills if f["type"] == "SELL"),
            "unpaired_buy_idx": is_open,
        },
        "oos_fill_counts": {
            "n": len(oos_fills),
            "buy": sum(1 for f in oos_fills if f["type"] == "BUY"),
            "sell": sum(1 for f in oos_fills if f["type"] == "SELL"),
            "unpaired_buy_idx": oos_open,
        },
        "is_pairs": is_pairs,
        "oos_pairs": oos_pairs,
        "is_pair_stats": side_stats(is_pairs),
        "oos_pair_stats": side_stats(oos_pairs),
        "all_pair_stats": side_stats(all_pairs),
        "concentration_is": concentration(is_pairs),
        "concentration_oos": concentration(oos_pairs),
        "concentration_all": concentration(all_pairs),
        "distribution": {
            "first_idx": min(idxs),
            "last_idx": max(idxs),
            "span_bars": max(idxs) - min(idxs),
            "is_first_half_0_699": sum(1 for f in is_fills if int(f["idx"]) < 700),
            "is_second_half_700_1399": sum(1 for f in is_fills if 700 <= int(f["idx"]) < 1400),
            "oos_first_half_1400_1699": sum(1 for f in oos_fills if int(f["idx"]) < 1700),
            "oos_second_half_1700_1999": sum(1 for f in oos_fills if int(f["idx"]) >= 1700),
            "official_equity_profit_after_drop_trade": "UNKNOWN — needs full close[] equity replay",
        },
        "consistency": {
            "is_profit": row["is"]["profit"],
            "oos_profit": row["oos"]["profit"],
            "oos_over_is_profit_descriptive": round(float(row["oos"]["profit"]) / float(row["is"]["profit"]), 4),
            "is_dd": row["is"]["max_drawdown"],
            "oos_dd": row["oos"]["max_drawdown"],
            "oos_over_is_dd_descriptive": round(float(row["oos"]["max_drawdown"]) / float(row["is"]["max_drawdown"]), 4),
            "is_events": row["is"]["total_trades"],
            "oos_events": row["oos"]["total_trades"],
        },
    }
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("WROTE", os.path.abspath(OUT))
    print("IS pairs", len(is_pairs), "OOS pairs", len(oos_pairs))
    print("IS conc", report["concentration_is"])
    print("OOS conc", report["concentration_oos"])
    print("ALL conc", report["concentration_all"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
