"""Write gold_follow/STATUS.json from frozen V4/V5 + latest GOLD_D1.csv."""
from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_gold_follow.stance import write_status  # noqa: E402


def main():
    st = write_status()
    print("STATUS", st.get("stance"), "since", st.get("since_entry"),
          "last", st.get("last_bar"), st.get("last_close"),
          "v5w", st.get("v5_weight"), "candidate", st.get("candidate"))
    return 0 if st.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
