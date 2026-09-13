"""Content hashes for experiment_id / data_hash / code_hash / result_hash."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_files(paths: Iterable[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(Path(p) for p in paths):
        if not path.is_file():
            continue
        h.update(path.as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def code_hash() -> str:
    here = Path(__file__).resolve().parent
    files = [p for p in here.glob("*.py") if p.name != "__pycache__"]
    return sha256_files(files)
