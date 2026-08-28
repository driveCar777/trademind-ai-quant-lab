"""Smoke: dashboard shows next-step Ask AI without auto-inference."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")


def main():
    failed = 0
    with open(DASH, "r", encoding="utf-8") as fh:
        html = fh.read()

    if 'id="nextAiBtn"' in html and "用这笔数字问 AI" in html:
        print("[PASS] next-step button present")
    else:
        print("[FAIL] missing 用这笔数字问 AI")
        failed += 1

    if "function goAskAi()" in html and "scrollIntoView" in html:
        print("[PASS] goAskAi only locates the card")
    else:
        print("[FAIL] goAskAi missing")
        failed += 1

    start = html.find("function fillAiFromTask")
    end = html.find("function buildAiBody")
    body = html[start:end] if start >= 0 and end > start else ""
    if body and "submitAI(" not in body and "fetch(" not in body:
        print("[PASS] fillAiFromTask does not call AI")
    else:
        print("[FAIL] fillAiFromTask looks like it sends AI")
        failed += 1

    go = html[html.find("function goAskAi()"):html.find("function fillAiFromTask")]
    if go and "submitAI(" not in go and "/api/v1/ai/" not in go:
        print("[PASS] goAskAi does not POST AI")
    else:
        print("[FAIL] goAskAi posts AI")
        failed += 1

    if "if (!aiOnline)" in html and "网页不能启动模型" in html:
        print("[PASS] offline blocks ask")
    else:
        print("[FAIL] missing offline guard")
        failed += 1

    if failed:
        print("SMOKE_10_FAIL")
        return 1
    print("SMOKE_10_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
