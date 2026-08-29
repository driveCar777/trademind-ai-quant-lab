"""Fail if likely secrets are in files that would be committed."""
from __future__ import print_function

import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIR = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "tmp",
    "ai-gateway",
    "docker-images",
    "monitor-binaries",
    "monitor-assets",
    "data/mine",
    "data/mt5_terminal",
    ".tmp",
}
FORBIDDEN = (
    "Auto@418",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
)
TOKEN_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,})")
HARD_PASS = re.compile(r"""password\s*=\s*["'][^"']{3,}["']""", re.I)


def skip(rel):
    parts = rel.replace("\\", "/").split("/")
    if parts[0] in SKIP_DIR:
        return True
    if rel.replace("\\", "/").startswith("tmp/"):
        return True
    if rel.replace("\\", "/").startswith("data/mt5_terminal/"):
        return True
    if rel.replace("\\", "/").startswith(".tmp/"):
        return True
    if rel.endswith(".example"):
        return True
    if rel.replace("\\", "/") == "scripts/secret_scan.py":
        return True
    return False


def main():
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR and not d.startswith(".")]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            if skip(rel):
                continue
            if name == ".env" or name.endswith(".env"):
                continue
            try:
                handle = open(path, "r", encoding="utf-8", errors="ignore")
                try:
                    text = handle.read(400000)
                finally:
                    handle.close()
            except Exception:
                continue
            for tok in FORBIDDEN:
                if tok in text:
                    hits.append((rel, tok[:8]))
            if TOKEN_RE.search(text):
                hits.append((rel, "token_like"))
            if HARD_PASS.search(text) and "TRADEMIND_XAVIER_PASSWORD" not in text:
                if name.endswith((".py", ".ps1", ".bat", ".md")):
                    hits.append((rel, "hardcoded_password_assign"))
    if hits:
        print("SECRET_SCAN_FAIL")
        for rel, why in hits[:80]:
            print(" ", rel, why)
        return 1
    print("SECRET_SCAN_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
