"""Exchange futures curve features. Ava CFD rows are rejected."""
from __future__ import print_function

from research_engine.v6_external.knowledge_time import (
    KnowledgeLeak,
    assert_feature_before_target,
    oi_knowledge_utc,
    session_date_utc,
    settlement_knowledge_utc,
)


BROKER_FORBIDDEN = (
    "GOLD",
    "OIL",
    "SILVER",
    "NATGAS",
    "GOLD_FUTURE",
    "SI_FUTURE",
    "CrudeTEST",
)


class NotExchangeFuture(ValueError):
    pass


def reject_broker_symbol(symbol):
    name = str(symbol or "").strip()
    if name in BROKER_FORBIDDEN or name.startswith("#"):
        raise NotExchangeFuture("Ava CFD %s is not an exchange future" % name)
    return True


def _as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    number = _as_float(value)
    if number is None:
        return None
    return int(number)


def group_by_session(rows):
    out = {}
    for row in rows:
        reject_broker_symbol(row.get("asset") or row.get("root") or row.get("symbol"))
        session = session_date_utc(row.get("session_date") or row.get("timestamp_utc"))
        if not session:
            continue
        out.setdefault(session, []).append(row)
    return out


def ranked_outrights(session_rows):
    ranked = []
    for row in session_rows:
        if str(row.get("instrument_class") or "F").upper() not in ("F", "FUTURE", ""):
            continue
        expiry = session_date_utc(row.get("expiry"))
        settle = _as_float(row.get("settlement") or row.get("close"))
        if not expiry or settle is None or settle <= 0:
            continue
        ranked.append(
            {
                "contract": row.get("contract") or row.get("raw_symbol"),
                "expiry": expiry,
                "settlement": settle,
                "close": _as_float(row.get("close")),
                "volume": _as_int(row.get("volume")),
                "open_interest": _as_int(row.get("open_interest")),
                "root": row.get("root") or row.get("asset"),
            }
        )
    ranked.sort(key=lambda item: item["expiry"])
    return ranked


def front_second(session_rows):
    ranked = ranked_outrights(session_rows)
    if len(ranked) < 2:
        return None
    return ranked[0], ranked[1]


def curve_slope(front, second):
    if not front or not second:
        return None
    if front["settlement"] <= 0:
        return None
    return (second["settlement"] - front["settlement"]) / front["settlement"]


def is_backwardation(slope):
    return slope is not None and slope < 0


def is_contango(slope):
    return slope is not None and slope > 0


def roll_yield(front, second):
    """Positive when front > deferred (backwardation / positive roll)."""
    if not front or not second:
        return None
    if second["settlement"] <= 0:
        return None
    return (front["settlement"] - second["settlement"]) / second["settlement"]


def session_features(session_rows, prev_slope=None, prev_front_oi=None):
    pair = front_second(session_rows)
    if pair is None:
        return None
    front, second = pair
    slope = curve_slope(front, second)
    oi = front.get("open_interest")
    oi_chg = None
    if oi is not None and prev_front_oi not in (None,):
        oi_chg = oi - prev_front_oi
    steepening = None
    if slope is not None and prev_slope is not None:
        steepening = slope - prev_slope
    session = session_date_utc(
        session_rows[0].get("session_date") or session_rows[0].get("timestamp_utc")
    )
    return {
        "session_date": session,
        "root": front.get("root"),
        "front": front["contract"],
        "second": second["contract"],
        "front_expiry": front["expiry"],
        "second_expiry": second["expiry"],
        "front_settle": front["settlement"],
        "second_settle": second["settlement"],
        "slope": slope,
        "backwardation": is_backwardation(slope),
        "contango": is_contango(slope),
        "roll_yield": roll_yield(front, second),
        "front_oi": oi,
        "front_oi_change": oi_chg,
        "steepening": steepening,
        "settlement_knowledge_utc": settlement_knowledge_utc(session),
        "oi_knowledge_utc": oi_knowledge_utc(session),
    }


def feature_panel(rows):
    grouped = group_by_session(rows)
    sessions = sorted(grouped.keys())
    out = []
    prev_slope = None
    prev_oi = None
    for session in sessions:
        feat = session_features(grouped[session], prev_slope, prev_oi)
        if feat is None:
            continue
        out.append(feat)
        prev_slope = feat.get("slope")
        prev_oi = feat.get("front_oi")
    return out


def attach_targets(features, next_front_returns):
    """next_front_returns: {session_date: (target_start_utc, ret)} after knowledge."""
    tagged = []
    for feat in features:
        know = feat["settlement_knowledge_utc"]
        nxt = next_front_returns.get(feat["session_date"])
        if not nxt:
            feat = dict(feat)
            feat["target_return"] = None
            tagged.append(feat)
            continue
        target_start, ret = nxt
        assert_feature_before_target(know, target_start)
        if session_date_utc(target_start) <= feat["session_date"]:
            raise KnowledgeLeak("same-session target forbidden")
        row = dict(feat)
        row["target_start_utc"] = target_start
        row["target_return"] = ret
        tagged.append(row)
    return tagged
