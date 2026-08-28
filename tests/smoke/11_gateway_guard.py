"""Smoke: gateway guards concurrency and prompt size. No live inference."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INF = os.path.join(ROOT, "ai-gateway", "inference.py")
SRV = os.path.join(ROOT, "ai-gateway", "server.py")
BAT = os.path.join(ROOT, "ai-gateway", "start_sycl.bat")


def main():
    failed = 0
    with open(INF, "r", encoding="utf-8") as fh:
        inf = fh.read()
    with open(SRV, "r", encoding="utf-8") as fh:
        srv = fh.read()
    with open(BAT, "r", encoding="utf-8") as fh:
        bat = fh.read()

    if "class EngineBusy" in inf and "acquire(blocking=False)" in inf:
        print("[PASS] generate lock rejects second caller")
    else:
        print("[FAIL] missing EngineBusy lock")
        failed += 1

    if "MAX_GEN_TOKENS = 1024" in inf and "MAX_MESSAGE_CHARS = 4000" in inf:
        print("[PASS] token / message caps present")
    else:
        print("[FAIL] missing caps")
        failed += 1

    if "EngineBusy" in srv and "AI Gateway busy" in srv:
        print("[PASS] server maps busy to 503")
    else:
        print("[FAIL] server missing busy 503")
        failed += 1

    if "max_tokens\", 2048)" in srv:
        print("[FAIL] generate still defaults to 2048")
        failed += 1
    else:
        print("[PASS] generate default is no longer 2048")

    if "GGML_SYCL_F16=OFF" in bat and "ONEAPI_DEVICE_SELECTOR" in bat and "Do not set" in bat:
        print("[PASS] start_sycl F16=OFF and warns against device selector")
    else:
        print("[FAIL] start_sycl.bat missing F16 guard")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "ai-gateway"))
    import inference as inference_mod
    eng = inference_mod.InferenceEngine(model_path="models/missing.gguf")
    long_msg = [{"role": "user", "content": "x" * 8000}]
    out = eng.prepare_messages(long_msg)
    if len(out) == 1 and len(out[0]["content"]) <= inference_mod.MAX_MESSAGE_CHARS + 20:
        print("[PASS] prepare_messages truncates")
    else:
        print("[FAIL] truncate %s" % (len(out[0]["content"]) if out else None))
        failed += 1

    if failed:
        print("SMOKE_11_FAIL")
        return 1
    print("SMOKE_11_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
