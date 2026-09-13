"""Outputs stay under live/paper_hot. Never the frozen paper journal."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
FROZEN_READ = ROOT / "data" / "market" / "research_engine" / "cn_a_share_ml_v25" / "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json"
B1_PATH = HOT / "B1_LEDGER.json"
B2_PATH = HOT / "B2_LEDGER.json"
B2_LOG = HOT / "B2_ANON_LOG.json"
B2_RUN = HOT / "B2_RUN.json"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"


def dump(path: Path, obj: Any) -> None:
    HOT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    tmp = path.with_name("%s.%s.%s.tmp" % (path.name, os.getpid(), threading.get_ident()))
    tmp.write_text(text, encoding="utf-8")
    last: Optional[Exception] = None
    for i in range(12):
        try:
            os.replace(str(tmp), str(path))
            return
        except OSError as exc:
            last = exc
            time.sleep(0.05 * (i + 1))
    path.write_text(text, encoding="utf-8")
    try:
        tmp.unlink()
    except OSError:
        if last:
            raise last


def load(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default
