"""Write-once product contracts. One model + one shell each. No search after the first run."""
from __future__ import annotations

from typing import Any, Dict, List

# Frozen LGBM for a single D1 series (a priori: ~2k–8k rows, not the V25 cross-section 1000-min-child).
LGBM_PARAMS = {
    "objective": "regression",
    "num_leaves": 15,
    "learning_rate": 0.03,
    "n_estimators": 200,
    "min_child_samples": 40,
    "colsample_bytree": 0.8,
    "subsample": 0.8,
    "subsample_freq": 1,
    "reg_lambda": 1.0,
    "num_threads": 4,
    "random_state": 25,
    "verbosity": -1,
}

CORE = ("R1", "R5", "R20", "VOL20", "VOL60", "ATR14", "DIST_SMA50", "DIST_SMA200", "RSI14", "GAP", "RANGE_ATR", "DOW")
SLIP = 0.0002
MIN_HIST = 220
REFIT_EVERY = 250
EMBARGO_EXTRA = 1
FIRST_PRED_BARS = 300
VAL_FRAC = 0.30  # last 30% of the long sample is the validation *report* window; scores stay walk-forward OOS
SPECIAL = (
    ("COVID_2020", "2020-02-01", "2020-06-30"),
    ("HIKING_2022", "2022-01-01", "2022-12-31"),
    ("RECENT_2024_ON", "2024-01-01", "2099-12-31"),
)

# Broker aliases for pull. SHARES / US stocks excluded by owner request.
PRODUCTS: Dict[str, Dict[str, Any]] = {
    "GOLD": {
        "label": "黄金",
        "logical": "XAUUSD",
        "aliases": ("GOLD", "XAUUSD"),
        "hold": 10,
        "features": CORE + ("MONTH",),
        "shell": "TREND_LS",
        "why": "隔夜便宜，允许 10 日持有；只用黄金自己的 OHLC，不用银/美元指数。",
    },
    "CRUDE": {
        "label": "原油",
        "logical": "CRUDE",
        "aliases": ("CrudeOIL", "WTICrude", "CRUDE"),
        "hold": 5,
        "features": CORE + ("REV5", "VOL_EXPAND"),
        "shell": "SHORT_HOLD_LS",
        "why": "双边年化约 −4.5%，只拿 5 日；反转与波动扩张是原油自己的价内特征。",
    },
    "EURUSD": {
        "label": "欧美",
        "logical": "EURUSD",
        "aliases": ("EURUSD",),
        "hold": 5,
        "features": CORE + ("R60",),
        "shell": "FX_LS",
        "why": "历史长、点差小；5 日进出，不用商品持有期。",
    },
    "USDJPY": {
        "label": "美日",
        "logical": "USDJPY",
        "aliases": ("USDJPY",),
        "hold": 5,
        "features": CORE + ("R60",),
        "shell": "FX_LS",
        "why": "日元常跟趋势走，但仍是它自己的价序列、5 日外壳，不套黄金 10 日。",
    },
    "GBPUSD": {
        "label": "美英",
        "logical": "GBPUSD",
        "aliases": ("GBPUSD",),
        "hold": 5,
        "features": CORE + ("R60",),
        "shell": "FX_LS",
        "why": "与欧美同外壳，模型分开拟合。",
    },
    "USDCAD": {
        "label": "美加",
        "logical": "USDCAD",
        "aliases": ("USDCAD",),
        "hold": 5,
        "features": CORE + ("R60",),
        "shell": "FX_LS",
        "why": "不加原油外生变量，避免和原油模型缠在一起。",
    },
    "USDCHF": {
        "label": "美瑞",
        "logical": "USDCHF",
        "aliases": ("USDCHF",),
        "hold": 5,
        "features": CORE + ("R60",),
        "shell": "FX_LS",
        "why": "避险货币对，仍只用自己的价，不拿黄金分数。",
    },
}


def product_ids() -> List[str]:
    return list(PRODUCTS.keys())
