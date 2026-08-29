"""Load TRADEMIND_* from process env or local .env. Never print secrets."""
from __future__ import print_function

import os

from research_engine.data_expansion.paths import repo_root
from research_engine.data_sources import ENV_DATABENTO


def _parse_dotenv(path):
    out = {}
    if not os.path.isfile(path):
        return out
    handle = open(path, "r")
    try:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key:
                out[key] = value
    finally:
        handle.close()
    return out


def _dotenv_paths():
    root = repo_root()
    return (
        os.path.join(root, ".env"),
        os.path.join(root, ".env.local"),
    )


def load_dotenv_if_present():
    loaded = False
    for path in _dotenv_paths():
        parsed = _parse_dotenv(path)
        if parsed:
            loaded = True
        for key, value in parsed.items():
            if not value:
                continue
            if key.startswith("TRADEMIND_") or key == "DATABENTO_API_KEY":
                if key not in os.environ:
                    os.environ[key] = value
    return loaded


def databento_api_key():
    load_dotenv_if_present()
    value = os.environ.get(ENV_DATABENTO) or os.environ.get("DATABENTO_API_KEY") or ""
    return value.strip()


def has_databento_key():
    return bool(databento_api_key())


def key_fingerprint(key=None):
    text = key if key is not None else databento_api_key()
    if not text:
        return ""
    return "len=%d last4=%s" % (len(text), text[-4:])
