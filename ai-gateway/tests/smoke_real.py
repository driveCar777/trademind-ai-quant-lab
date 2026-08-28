"""Real smoke for AI Gateway V3.0.

Requires the gateway already running on :9100 (use start_sycl.bat).
This is not a mock: it calls the live Qwen2.5-14B-Instruct endpoints.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python smoke_real.py` from ai-gateway/tests
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_server import (  # noqa: E402
    test_chat,
    test_describe,
    test_generate,
    test_health,
    test_models,
    test_signal,
)


def test_model_is_qwen(chat_data):
    reply = (chat_data.get("data") or {}).get("reply", "")
    lowered = reply.lower()
    if "qwen" not in lowered and "通义" not in reply:
        print(f"[WARN] chat reply did not self-identify as Qwen: {reply[:120]}")
        return
    print("[PASS] model self-identify contains Qwen")


def main():
    print("=" * 60)
    print("  AI Gateway V3.0 Real Smoke (Qwen2.5-14B-Instruct)")
    print("  Target: http://127.0.0.1:9100")
    print("=" * 60)

    steps = [
        ("Health", test_health),
        ("Models", test_models),
        ("Chat", test_chat),
        ("Generate", test_generate),
        ("Describe", test_describe),
        ("Signal", test_signal),
    ]
    passed = 0
    failed = 0
    chat_data = None
    for name, fn in steps:
        try:
            result = fn()
            if name == "Chat":
                chat_data = result
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {name} - {exc}")
            failed += 1

    if chat_data:
        test_model_is_qwen(chat_data)

    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
