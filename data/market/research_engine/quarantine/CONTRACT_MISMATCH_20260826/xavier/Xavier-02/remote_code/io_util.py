from __future__ import print_function

import json
import os

from research_engine.errors import ResultImmutableError
from research_protocol.hashing import canonical_hash


def dump_json(path, payload):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def write_once(path, payload):
    if os.path.exists(path):
        raise ResultImmutableError(path)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".tmp"
    handle = open(tmp, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    os.rename(tmp, path)


def write_text_once(path, text):
    if os.path.exists(path):
        raise ResultImmutableError(path)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()


def load_json(path):
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def payload_hash(payload):
    return canonical_hash(payload)
