# Post-V21 Disk Walk — W2

**Date:** 2026-09-04  
**Method:** `os.walk` over `data/market/cn_a_share/` (5597 dirs, 11605 files listed) and `data/market/research_engine/` (2272 dirs, 6974 files). Per-file type / line count / json keys recorded. No BaoStock login.  
**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/DISK_WALK.json`  
**Script:** `research_engine/post_v21_w2_walk.py`

```
AVAILABLE                = 0
NEW_INFORMATION_CLASS    = NONE   (issued after the table below)
announcements/           = ['.gitkeep'] only
financial UNAVAILABLE    = debt_ratio, roa
financial quarterly      = not downloaded
daily raw columns        = date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST
                           (no peTTM / pbMRQ / psTTM — never pulled)
```

## Object table (one row per object)

| Dir | Files / size | Content | Mechanism | PIT | Consumed by | Status |
|---|---|---|---|---|---|---|
| `raw/daily_panel_v12_1/symbols/*` | ~5.5k symbols × 4 (raw.csv, qfq.csv, adjust_factor.json, meta.json) | OHLC, preclose, volume, amount, turn, tradestatus, pctChg, isST | daily bars | YES | V12.2 → V13–V21 | ALREADY_TESTED |
| `alpha_cache/v13_000002` | 14 npy (~1.7 GB) | open/high/low/close/preclose/volume/amount/turn/isST/listed/tradestatus | frozen panel arrays | YES | V13–V21 | ALREADY_TESTED |
| `raw/daily_panel_v12_1/symbols/*/adjust_factor.json` | per symbol | adjust factors (CA) | corporate-action representation | YES | V14.1 CA audit (DIVIDEND_EXCLUSION noted) | NOT_A_SIGNAL |
| `raw/basics`, `reference/` | BASIC 8928 rows, CALENDAR 13039, UNIVERSE_HIST 8715 | listing / delisting / ST / status | eligibility, age | YES | V12, V18 | ALREADY_TESTED |
| `financial/normalized` | FINANCIAL_ANNUAL.csv 64440 rows, 5500 symbols | net profit, revenue, ROE, GPM, NPM, EPS(TTM vendor) | annual ratio after announce | YES (restatement risk) | V16 F1–F6 | ALREADY_TESTED |
| `financial/raw/profit` | 5540 files | profit API only | — | — | V16 | ALREADY_TESTED |
| `financial/raw/balance` | **empty** | balance API never pulled (`debt_ratio`, `roa` UNAVAILABLE) | leverage ratio | would need login | none | LOW_VALUE (ratio twin of V16; locked) |
| `industry/normalized` + `raw/monthly` (171) | 81 MB | monthly as-of industry | membership | YES | V16 I1–I3, V19 IM1–IM6 | ALREADY_TESTED |
| `index/normalized` + `raw/monthly` (342) | 11.6 MB | HS300 / ZZ500 monthly as-of | membership / add-drop | YES | V20 X1–X4 | ALREADY_TESTED |
| `dividend/normalized` + `raw` (5550) | 1.9 MB + 22 MB | cash/stock plan, announce date | announce window | YES | V21 D1/D2 | ALREADY_TESTED |
| `announcements/` | `.gitkeep` | nothing | filing window | — | none | EMPTY (locked: not V22) |
| `corporate_actions/` | 1 sample json | CA sample | representation | sample | V14.1 | NOT_A_SIGNAL |
| `quality/`, `research/`, `manifests/`, top-level `A_SHARE_*.json` | 20 + 5 + 11 | panel QA, hashes, PIT tests | not a signal | — | V12 | NOT_A_SIGNAL |
| `research_engine/*` (2272 dirs) | RESULTS / EQUITY / TRADES / DECISION per version | outputs | — | — | V8–V21 | OUTPUT_NOT_INPUT |
| BaoStock daily `peTTM/pbMRQ/psTTM/pcfNcfTTM` | **not on disk** | valuation ratios | slow ratio (value tilt) | would be | none | LOW_VALUE + requires login (locked). Same object class as V16 ratios; value ≈ low-vol/size neighborhood already dead |

## Reading

Every input object on disk has been consumed by a V13–V21 contract, or is QA/CA representation that is not a signal class. The two things *not* on disk (balance-sheet leverage, price valuation ratios) are both **ratios** — the object class the lock names as not new — and both require a BaoStock login that is not permitted in this session.

**AVAILABLE = 0 on disk. NONE.** Q3-style implementation is not triggered from disk. Next: W3 failure atlas.

**Addendum (same day, after user authorised spending and autonomous continuation):** a *network* probe — not a disk walk — found a free, PIT-able, non-ratio / non-membership / non-announcement object that was never on disk: exchange-published daily **margin detail (融资融券)** per stock, 2010-03-31 →, via SSE/SZSE official endpoints and the Eastmoney datacenter mirror. This triggers the W2 "真·新对象 → 先实现到 Decision（≤3 条）" branch as **V23**. See `V23_MARGIN_CONTRACT.md`. Holder count and HKEX northbound holdings are also reachable and queued behind V23.
