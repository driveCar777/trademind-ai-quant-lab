"""Knowledge time for exchange futures / options / macro. No same-session leak."""
from __future__ import print_function

from datetime import datetime, timedelta


ISO_Z = "%Y-%m-%dT%H:%M:%SZ"
DATE = "%Y-%m-%d"

# After US afternoon settlement window. Conservative for D1 research.
SETTLEMENT_HOUR_UTC = 21
# CME publishes cleared volume / OI on the following UTC date (Friday -> Sunday).
OI_LAG_DAYS = 1


class KnowledgeLeak(ValueError):
    pass


def _parse_date(text):
    raw = str(text or "").strip()
    if not raw:
        return None
    if "T" in raw:
        raw = raw.split("T", 1)[0]
    try:
        return datetime.strptime(raw[:10], DATE)
    except ValueError:
        return None


def session_date_utc(text):
    parsed = _parse_date(text)
    if parsed is None:
        return ""
    return parsed.strftime(DATE)


def settlement_knowledge_utc(session_date):
    parsed = _parse_date(session_date)
    if parsed is None:
        return ""
    stamped = parsed.replace(hour=SETTLEMENT_HOUR_UTC, minute=0, second=0)
    return stamped.strftime(ISO_Z)


def oi_knowledge_utc(session_date):
    parsed = _parse_date(session_date)
    if parsed is None:
        return ""
    stamped = (parsed + timedelta(days=OI_LAG_DAYS)).replace(
        hour=SETTLEMENT_HOUR_UTC, minute=0, second=0
    )
    return stamped.strftime(ISO_Z)


def definition_knowledge_utc(ts_event):
    raw = str(ts_event or "").strip()
    if not raw:
        return ""
    if "T" in raw:
        body = raw.replace("Z", "")[:19]
        try:
            datetime.strptime(body, "%Y-%m-%dT%H:%M:%S")
            return body + "Z"
        except ValueError:
            pass
    session = session_date_utc(raw)
    return settlement_knowledge_utc(session) if session else ""


def assert_feature_before_target(knowledge_utc, target_start_utc):
    if not knowledge_utc or not target_start_utc:
        raise KnowledgeLeak("missing knowledge or target timestamp")
    if str(knowledge_utc) >= str(target_start_utc):
        raise KnowledgeLeak(
            "knowledge_time %s is not strictly before target %s"
            % (knowledge_utc, target_start_utc)
        )
    return True


def same_session_forbidden(session_date, target_session_date):
    return session_date_utc(session_date) == session_date_utc(target_session_date)


def next_session_target_start(knowledge_utc):
    body = str(knowledge_utc or "").replace("Z", "")[:19]
    know = datetime.strptime(body, "%Y-%m-%dT%H:%M:%S")
    nxt = (know + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    return nxt.strftime(ISO_Z)
