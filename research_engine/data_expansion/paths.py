"""Resolve factory JSON without hardcoding a drive letter."""
from __future__ import print_function

import os


def repo_root():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def expansion_dir():
    return os.path.join(repo_root(), "data", "market", "research_engine", "data_expansion")


def sources_dir():
    return os.path.join(repo_root(), "data", "market", "research_engine", "data_sources")


def load_json(folder, name):
    path = os.path.join(folder, name)
    handle = open(path, encoding="utf-8")
    try:
        import json

        return json.load(handle)
    finally:
        handle.close()
