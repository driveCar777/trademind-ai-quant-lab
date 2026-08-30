"""A-share data roots on D:. Large raw files stay out of Git."""
from __future__ import print_function

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE = os.path.join(ROOT, "data", "market", "cn_a_share")
RAW = os.path.join(BASE, "raw")
NORMALIZED = os.path.join(BASE, "normalized")
REFERENCE = os.path.join(BASE, "reference")
CORP = os.path.join(BASE, "corporate_actions")
FINANCIAL = os.path.join(BASE, "financial")
ANNOUNCE = os.path.join(BASE, "announcements")
MANIFESTS = os.path.join(BASE, "manifests")
QUALITY = os.path.join(BASE, "quality")
RESEARCH = os.path.join(BASE, "research")
TMP = os.path.join(ROOT, ".tmp", "cn_a_share")
DOCS = os.path.join(ROOT, "docs", "research_engine")
SUBDIRS = (RAW, NORMALIZED, REFERENCE, CORP, FINANCIAL, ANNOUNCE, MANIFESTS, QUALITY, RESEARCH)


def ensure_tree():
    for path in SUBDIRS + (TMP,):
        if not os.path.isdir(path):
            os.makedirs(path)
    return BASE
