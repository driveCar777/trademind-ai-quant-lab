"""Xavier SSH credentials. Env only. No hardcoded password."""
from __future__ import print_function

import os

_DOTENV_LOADED = False


class XavierAuthError(RuntimeError):
    pass


def _load_dotenv():
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return
    handle = open(path, "r", encoding="utf-8")
    try:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key.startswith("TRADEMIND_") and key not in os.environ:
                os.environ[key] = value
            if key == "RABBITMQ_PASS" and "TRADEMIND_XAVIER_PASSWORD" not in os.environ and value:
                os.environ["TRADEMIND_XAVIER_PASSWORD"] = value
    finally:
        handle.close()


def xavier_user():
    _load_dotenv()
    user = os.environ.get("TRADEMIND_XAVIER_USER") or os.environ.get("TRADEMIND_SSH_USER")
    if user:
        return user
    return "dji"


def xavier_password():
    _load_dotenv()
    password = os.environ.get("TRADEMIND_XAVIER_PASSWORD") or os.environ.get("TRADEMIND_SSH_PASSWORD")
    if not password:
        raise XavierAuthError("TRADEMIND_XAVIER_PASSWORD is required")
    return password
