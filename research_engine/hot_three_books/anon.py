"""Anonymous OHLC windows. No tickers, names, calendar dates, or volume in the payload."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

LOOKBACK = 60
PROTOCOL = "v1.1"  # v1.0: bars as {d,o,h,l,c} objects, 4 dp. v1.1 (2026-09-11): bars as [o,h,l,c] arrays, 2 dp, index implicit. Same information, ~half the bytes.
DECIMALS = 2
LEAK = re.compile(
    r"(sh\.|sz\.|bj\.|SH\.|SZ\.|"
    r"(?<![A-Za-z0-9])\d{6}(?![A-Za-z0-9])|"
    r"\d{4}-\d{2}-\d{2}|"
    r"[\u4e00-\u9fff])"
)


def leak_hits(text: str) -> List[str]:
    return [m.group(0) for m in LEAK.finditer(text or "")]


def assert_clean(obj: Any) -> str:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    hits = leak_hits(text)
    if hits:
        raise ValueError("ANON_LEAK " + ",".join(hits[:8]))
    return text


def _first_close(closes: np.ndarray) -> float:
    for x in closes:
        v = float(x)
        if np.isfinite(v) and v > 0:
            return v
    return 0.0


def _px(v: float, scale: float) -> float:
    if not np.isfinite(v) or v <= 0 or scale <= 0:
        return 0.0
    return round(100.0 * float(v) / scale, DECIMALS)


def pack_window(pack: Dict[str, Any], t: int, js: Sequence[int], lookback: int = LOOKBACK) -> Tuple[Dict[str, Any], Dict[str, str]]:
    t0 = max(0, int(t) - lookback + 1)
    mapping: Dict[str, str] = {}
    series: List[Dict[str, Any]] = []
    symbols = pack["symbols"]
    for i, j in enumerate(js):
        uid = "U%02d" % (i + 1)
        mapping[uid] = str(symbols[int(j)])
        o = np.asarray(pack["open"][t0 : t + 1, int(j)], dtype=float)
        h = np.asarray(pack["high"][t0 : t + 1, int(j)], dtype=float)
        l = np.asarray(pack["low"][t0 : t + 1, int(j)], dtype=float)
        c = np.asarray(pack["close"][t0 : t + 1, int(j)], dtype=float)
        scale = _first_close(c)
        bars = []
        for k in range(c.shape[0]):
            bars.append([_px(float(o[k]), scale), _px(float(h[k]), scale), _px(float(l[k]), scale), _px(float(c[k]), scale)])
        series.append({"id": uid, "bars": bars})
    payload = {"protocol": PROTOCOL, "cols": ["o", "h", "l", "c"], "series": series}
    assert_clean(payload)
    return payload, mapping


def parse_keep(text: str, valid_ids: Sequence[str]) -> List[str]:
    if not text:
        return []
    block = text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        block = m.group(1)
    else:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            block = text[a : b + 1]
    try:
        obj = json.loads(block)
    except ValueError:
        return []
    raw = obj.get("keep") if isinstance(obj, dict) else None
    if not isinstance(raw, list):
        return []
    allowed = set(valid_ids)
    out = []
    for x in raw:
        s = str(x).strip().upper()
        if s in allowed and s not in out:
            out.append(s)
        elif str(x).strip() in allowed and str(x).strip() not in out:
            out.append(str(x).strip())
    return out


PROMPT = (
    "You receive anonymous daily OHLC series. Each series is normalized so the first close is 100. "
    "bars is a list of [open, high, low, close] in time order (oldest first, one bar per trading day). "
    "Do not search the web. Do not guess tickers, company names, industries, or calendar dates. "
    "Do not mention any stock code.\n"
    "Return only one JSON object: {\"keep\":[\"U01\"]}\n"
    "keep is a subset of the series ids (may be empty). "
    "Choose series you would hold about 20 trading days in a long-only book.\n"
    "data:\n"
)
