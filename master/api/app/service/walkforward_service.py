"""V11: split MT5 closes and judge risk. Master does not compute PnL."""

from __future__ import print_function

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

IS_RATIO = 0.7
MIN_BARS = 200
MAX_DD_PCT = 25.0
MIN_TRADES = 5
SLIPPAGE_BPS = 10
COMMISSION_BPS = 5
STRATEGY = "RSI"
BASKET = ("RSI", "EMA_MACD", "SMA_CROSS", "BOLLINGER", "TURTLE", "REGIME_SWITCH")
CANDIDATES = (
    {"id": "rsi-14-30-70", "strategy": "RSI", "params": {"period": 14, "oversold": 30, "overbought": 70}},
    {"id": "rsi-10-25-70", "strategy": "RSI", "params": {"period": 10, "oversold": 25, "overbought": 70}},
    {"id": "rsi-21-30-75", "strategy": "RSI", "params": {"period": 21, "oversold": 30, "overbought": 75}},
    {"id": "rsi-14-25-75", "strategy": "RSI", "params": {"period": 14, "oversold": 25, "overbought": 75}},
    {"id": "macd-12-26-9", "strategy": "EMA_MACD", "params": {}},
    {"id": "sma-20-50", "strategy": "SMA_CROSS", "params": {"fast": 20, "slow": 50}},
    {"id": "sma-10-40", "strategy": "SMA_CROSS", "params": {"fast": 10, "slow": 40}},
    {"id": "sma-15-60", "strategy": "SMA_CROSS", "params": {"fast": 15, "slow": 60}},
    {"id": "boll-20-2", "strategy": "BOLLINGER", "params": {"period": 20, "num_std": 2.0}},
    {"id": "boll-15-2", "strategy": "BOLLINGER", "params": {"period": 15, "num_std": 2.0}},
    {"id": "turtle", "strategy": "TURTLE", "params": {}},
    {"id": "regime", "strategy": "REGIME_SWITCH", "params": {}},
)
VERDICT_LABELS = {
    "falsified": "证伪",
    "risk_fail": "风控淘汰",
    "insufficient": "样本不足",
    "survived": "本次未证伪",
}


def split_closes(closes: List[float]) -> Tuple[List[float], List[float]]:
    if len(closes) < MIN_BARS:
        raise ValueError("bars")
    cut = int(len(closes) * IS_RATIO)
    if cut < 50 or len(closes) - cut < 50:
        raise ValueError("bars")
    return list(closes[:cut]), list(closes[cut:])


def judge(is_row: Dict[str, Any], oos_row: Dict[str, Any]) -> str:
    if is_row.get("error") or oos_row.get("error"):
        return "insufficient"
    if (is_row.get("total_trades") or 0) < MIN_TRADES or (oos_row.get("total_trades") or 0) < MIN_TRADES:
        return "insufficient"
    if (is_row.get("max_drawdown") or 0) > MAX_DD_PCT or (oos_row.get("max_drawdown") or 0) > MAX_DD_PCT:
        return "risk_fail"
    if (oos_row.get("profit") or 0) <= 0:
        return "falsified"
    return "survived"


def score_is(is_row: Dict[str, Any]) -> Optional[float]:
    if (is_row.get("total_trades") or 0) < MIN_TRADES:
        return None
    if (is_row.get("max_drawdown") or 0) > MAX_DD_PCT:
        return None
    return round(float(is_row.get("profit") or 0) - 0.3 * float(is_row.get("max_drawdown") or 0), 4)


def pick_is(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    ranked = [row for row in rows if row.get("is_score") is not None]
    if not ranked:
        return None
    ranked.sort(key=lambda item: float(item.get("is_score") or -9999), reverse=True)
    return ranked[0]


def payload_for(
    symbol: str,
    closes: List[float],
    tag: str,
    cut: Optional[int] = None,
    strategy: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    body = {
        "strategy": strategy or STRATEGY,
        "symbol": symbol,
        "start": "mt5-%s" % tag,
        "close": closes,
        "slippage_bps": SLIPPAGE_BPS,
        "commission_bps": COMMISSION_BPS,
    }
    if cut is not None:
        body["cut"] = int(cut)
    if params:
        body["params"] = dict(params)
    return body


def format_bar_time(ts: Any) -> str:
    try:
        value = int(ts)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    return datetime.utcfromtimestamp(value).strftime("%Y-%m-%d %H:%M")


def window_of(times: List[Any]) -> Tuple[str, str]:
    if not times:
        return "", ""
    return format_bar_time(times[0]), format_bar_time(times[-1])


def stamp_trades(trades: List[Dict[str, Any]], times: List[Any], split: str) -> List[Dict[str, Any]]:
    rows = []
    for item in trades or []:
        raw_idx = item.get("idx")
        if raw_idx is None:
            continue
        try:
            idx = int(raw_idx)
        except (TypeError, ValueError):
            continue
        ts = times[idx] if 0 <= idx < len(times) else 0
        rows.append({
            "split": split,
            "side": item.get("type") or item.get("side") or "",
            "idx": idx,
            "time": format_bar_time(ts),
            "price": item.get("price"),
            "pnl_pct": item.get("pnl_pct"),
            "regime": item.get("regime") or "",
        })
    return rows


def attribute_regimes(strategy: str, body: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for split, key in (("样本内", "is"), ("样本外", "oos")):
        opened = None
        for item in ((body.get(key) or {}).get("trades") or []):
            if (item.get("type") or item.get("side")) == "BUY":
                opened = item.get("regime") or "range"
            elif (item.get("type") or item.get("side")) == "SELL":
                rows.append({
                    "strategy": strategy,
                    "split": split,
                    "regime": opened or item.get("regime") or "range",
                    "pnl_pct": item.get("pnl_pct"),
                })
                opened = None
    return rows


def fold_regimes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cells = {}
    for row in rows:
        key = (row.get("strategy"), row.get("regime"), row.get("split"))
        cell = cells.setdefault(key, {
            "strategy": row.get("strategy"),
            "regime": row.get("regime"),
            "split": row.get("split"),
            "n": 0,
            "pnl": 0.0,
        })
        if row.get("pnl_pct") is None:
            continue
        cell["n"] += 1
        cell["pnl"] = round(cell["pnl"] + float(row.get("pnl_pct") or 0), 2)
    return [cells[k] for k in sorted(cells)]


def describe(result: Dict[str, Any]) -> str:
    label = VERDICT_LABELS.get(result.get("verdict") or "", result.get("verdict") or "")
    return (
        "数字以摘要为准，不是模型编的。\n"
        "K 线窗口 %s ～ %s，周期 %s，共 %s 根。来自本机 MT5，仓库不另存整段行情。\n"
        "连续持仓：样本外接着样本内的仓位，切分不强平。\n"
        "行情分段（冻结）：上涨均线 / 震荡布林 / 下跌空仓。特征是相对均线偏离，不用张量训练。\n"
        "K 线分段 上%s 下%s 震%s。\n"
        "样本内：收益 %s%%，回撤 %s%%，成交 %s。\n"
        "样本外：收益 %s%%，回撤 %s%%，成交 %s。\n"
        "成交明细 %s 笔见下方表格（时间+价格）。没有表格就还没留下买卖点。\n"
        "判定：%s。survived 只表示这次没被证伪；样本内亏损就不能当买卖依据。\n"
        "第 3、4 步不能挂这张回测单。要下单先跑黄金 MT5 指标研究。"
        % (
            result.get("window_from") or "—",
            result.get("window_to") or "—",
            result.get("timeframe") or "—",
            result.get("bars") or "—",
            (result.get("regime_counts") or {}).get("up", "—"),
            (result.get("regime_counts") or {}).get("down", "—"),
            (result.get("regime_counts") or {}).get("range", "—"),
            result.get("is_profit", "—"),
            result.get("is_drawdown", "—"),
            result.get("is_trades", "—"),
            result.get("oos_profit", "—"),
            result.get("oos_drawdown", "—"),
            result.get("oos_trades", "—"),
            len(result.get("trades") or []),
            label,
        )
    )


def summarize(symbol: str, verdict: str, is_row: Dict[str, Any], oos_row: Dict[str, Any], bars: int, timeframe: str, strategy: str = "RSI") -> str:
    label = VERDICT_LABELS.get(verdict, verdict)
    return "%s %s %s 根=%s/%s 内%s外%s 回撤%s/%s 成交%s/%s" % (
        symbol,
        strategy,
        label,
        bars,
        timeframe,
        is_row.get("profit", "—"),
        oos_row.get("profit", "—"),
        is_row.get("max_drawdown", "—"),
        oos_row.get("max_drawdown", "—"),
        is_row.get("total_trades", "—"),
        oos_row.get("total_trades", "—"),
    )
