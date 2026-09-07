"""W2: os.walk inventory of data/market/cn_a_share and data/market/research_engine. Read-only."""
from __future__ import print_function

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CN = os.path.join(ROOT, "data", "market", "cn_a_share")
RE = os.path.join(ROOT, "data", "market", "research_engine")
AD = os.path.join(RE, "POST_V21_AUTODRIVE")

# Map of research_engine subdirs to the contract/version that consumed them
CONTRACT_MAP = {
    "cn_a_share_alpha_v1": "V13", "cn_a_share_alpha_v13_1": "V13.1",
    "cn_a_share_strategy_v14": "V14", "cn_a_share_strategy_v14_1": "V14.1",
    "cn_a_share_alpha_v2": "V15", "cn_a_share_information_v16": "V16",
    "cn_a_share_macro_v17": "V17", "cn_a_share_altinfo_v18": "V18",
    "cn_a_share_indmacro_v19": "V19", "cn_a_share_index_v20": "V20",
    "cn_a_share_div_v21": "V21",
}
CN_MAP = {
    "financial": "V16", "industry": "V16/V19", "index": "V20", "dividend": "V21",
    "normalized": "V12.2 panel -> V13-V21", "reference": "V12/V18 eligibility",
    "manifests": "V12", "quality": "V12", "research": "V12", "corporate_actions": "V14.1 CA audit (sample)",
    "announcements": "NONE", "raw": "V12 raw (gitignored)",
}


def quick_size(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                return {"type": "json_dict", "keys": len(obj), "top": sorted(obj.keys())[:8]}
            if isinstance(obj, list):
                return {"type": "json_list", "n": len(obj)}
            return {"type": "json_scalar"}
        if ext in (".csv", ".txt", ".md"):
            n = 0
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    n += 1
            return {"type": ext[1:], "lines": n}
    except Exception as e:  # noqa
        return {"type": ext[1:] or "bin", "error": str(e)[:60]}
    return {"type": ext[1:] or "bin", "bytes": os.path.getsize(path)}


def walk(base, contract_map, max_files_per_dir=60):
    rows = []
    dir_rows = []
    if not os.path.isdir(base):
        return rows, dir_rows
    for dp, dns, fns in os.walk(base):
        rel = os.path.relpath(dp, base).replace("\\", "/")
        top = rel.split("/")[0] if rel != "." else "."
        contract = contract_map.get(top, "UNMAPPED")
        fns_sorted = sorted(fns)
        total_bytes = 0
        for fn in fns_sorted:
            try:
                total_bytes += os.path.getsize(os.path.join(dp, fn))
            except OSError:
                pass
        dir_rows.append({
            "dir": rel, "n_files": len(fns), "n_subdirs": len(dns),
            "bytes": total_bytes, "contract": contract,
            "empty": len(fns) == 0 or (len(fns) == 1 and fns[0] == ".gitkeep"),
        })
        for fn in fns_sorted[:max_files_per_dir]:
            p = os.path.join(dp, fn)
            if fn == ".gitkeep":
                rows.append({"dir": rel, "file": fn, "size": {"type": "gitkeep", "bytes": os.path.getsize(p)}, "contract": contract})
                continue
            if os.path.getsize(p) > 50 * 1024 * 1024:
                rows.append({"dir": rel, "file": fn, "size": {"type": "large", "bytes": os.path.getsize(p)}, "contract": contract})
                continue
            rows.append({"dir": rel, "file": fn, "size": quick_size(p), "contract": contract})
        if len(fns_sorted) > max_files_per_dir:
            rows.append({"dir": rel, "file": "...", "size": {"type": "truncated", "n_more": len(fns_sorted) - max_files_per_dir}, "contract": contract})
    return rows, dir_rows


def financial_unavailable():
    p = os.path.join(CN, "financial", "reference", "FINANCIAL_CATALOG.json")
    out = {"path": p, "unavailable_fields": [], "note": None}
    if not os.path.isfile(p):
        out["note"] = "missing"
        return out
    try:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:  # noqa
        out["note"] = str(e)[:80]
        return out

    def rec(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and "UNAVAILABLE" in v.upper():
                    out["unavailable_fields"].append(path + "/" + k + "=" + v)
                elif k.upper() in ("UNAVAILABLE", "NOT_AVAILABLE", "BLOCKED") and v:
                    out["unavailable_fields"].append(path + "/" + k + "=" + json.dumps(v)[:120])
                else:
                    rec(v, path + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o[:200]):
                rec(v, path + "[%d]" % i)
    rec(obj)
    return out


def main():
    if not os.path.isdir(AD):
        os.makedirs(AD)
    cn_rows, cn_dirs = walk(CN, CN_MAP)
    re_rows, re_dirs = walk(RE, CONTRACT_MAP)
    ann = os.path.join(CN, "announcements")
    ann_files = sorted(os.listdir(ann)) if os.path.isdir(ann) else None
    fin_un = financial_unavailable()
    sa = os.path.join(RE, "cn_a_share_information_v16", "SOURCE_AUDIT.json")
    sa_keys = None
    if os.path.isfile(sa):
        with open(sa, "r", encoding="utf-8") as f:
            sa_keys = sorted(json.load(f).keys())

    # object table
    objects = [
        {"object": "normalized/ EQUITY D1 bars", "dir": "cn_a_share/normalized", "mechanism": "daily price/volume/amount", "pit": "YES", "contract": "V13-V21", "status": "ALREADY_TESTED"},
        {"object": "reference/ universe/basic/calendar", "dir": "cn_a_share/reference", "mechanism": "listing/ST/status", "pit": "YES", "contract": "V18 + eligibility", "status": "ALREADY_TESTED"},
        {"object": "financial/ annual ratios", "dir": "cn_a_share/financial", "mechanism": "annual statements after announce", "pit": "YES", "contract": "V16", "status": "ALREADY_TESTED"},
        {"object": "industry/ monthly membership", "dir": "cn_a_share/industry", "mechanism": "as-of industry", "pit": "YES", "contract": "V16/V19", "status": "ALREADY_TESTED"},
        {"object": "index/ HS300/ZZ500", "dir": "cn_a_share/index", "mechanism": "membership/add-drop", "pit": "YES", "contract": "V20", "status": "ALREADY_TESTED"},
        {"object": "dividend/ announce events", "dir": "cn_a_share/dividend", "mechanism": "cash/stock plan announce", "pit": "YES", "contract": "V21", "status": "ALREADY_TESTED"},
        {"object": "announcements/", "dir": "cn_a_share/announcements", "mechanism": "filings", "pit": "n/a", "contract": "NONE", "status": "EMPTY_DIR" if (ann_files in (None, [], [".gitkeep"])) else "HAS_FILES_REVIEW"},
        {"object": "corporate_actions/ sample", "dir": "cn_a_share/corporate_actions", "mechanism": "CA representation", "pit": "sample", "contract": "V14.1 audit", "status": "LOW_VALUE"},
        {"object": "quality/ + research/ + manifests/", "dir": "cn_a_share/*", "mechanism": "panel QA, not signal", "pit": "n/a", "contract": "V12", "status": "NOT_A_SIGNAL"},
        {"object": "research_engine MT5 frozen series (macro)", "dir": "research_engine/*", "mechanism": "EURUSD/US500/GVZ", "pit": "published", "contract": "V17/V19", "status": "ALREADY_TESTED"},
    ]
    available = [o for o in objects if o["status"] == "AVAILABLE"]
    payload = {
        "id": "POST_V21_DISK_WALK",
        "read_only": True,
        "cn_a_share_dirs": cn_dirs,
        "cn_a_share_files": cn_rows,
        "research_engine_dirs": re_dirs,
        "research_engine_files_n": len(re_rows),
        "research_engine_files": re_rows,
        "announcements_listing": ann_files,
        "financial_catalog_unavailable": fin_un,
        "source_audit_top_keys": sa_keys,
        "objects": objects,
        "n_available": len(available),
        "new_information_class": "NONE" if not available else "SEE_OBJECTS",
    }
    outp = os.path.join(AD, "DISK_WALK.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", outp)
    print("cn dirs", len(cn_dirs), "cn files", len(cn_rows))
    print("re dirs", len(re_dirs), "re files", len(re_rows))
    print("announcements", ann_files)
    print("fin unavailable", fin_un["unavailable_fields"][:10], fin_un["note"])
    print("source_audit keys", sa_keys)
    for d in cn_dirs:
        print("CN", d["dir"], d["n_files"], d["bytes"], d["contract"], "EMPTY" if d["empty"] else "")
    unm = sorted(set(d["dir"].split("/")[0] for d in re_dirs if d["contract"] == "UNMAPPED"))
    print("re unmapped top", unm)


if __name__ == "__main__":
    main()
