"""Xavier SSH credentials. Env only. No hardcoded password."""
from __future__ import print_function

import os


class XavierAuthError(RuntimeError):
    pass


def xavier_user():
    user = os.environ.get("TRADEMIND_XAVIER_USER") or os.environ.get("TRADEMIND_SSH_USER")
    if user:
        return user
    return "dji"


def xavier_password():
    password = os.environ.get("TRADEMIND_XAVIER_PASSWORD") or os.environ.get("TRADEMIND_SSH_PASSWORD")
    if not password:
        raise XavierAuthError("TRADEMIND_XAVIER_PASSWORD is required")
    return password
