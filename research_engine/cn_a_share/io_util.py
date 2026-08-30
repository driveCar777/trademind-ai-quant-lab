"""Small JSON/CSV helpers. Deterministic dumps."""
from __future__ import print_function

import csv
import json
import os

from research_protocol.hashing import canonical_hash, file_sha256


def dump_json(path, payload, sort_keys=True):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=sort_keys, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    return {"path": path, "sha256": file_sha256(path), "canonical_hash": canonical_hash(payload)}


def load_json(path):
    handle = open(path, "r", encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def write_csv(path, fieldnames, rows):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()
    return {"path": path, "sha256": file_sha256(path)}
