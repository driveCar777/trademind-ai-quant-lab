# V6 External Exchange Data — Phase report (recon + acquire-ready)

Date: **2026-08-29**
Mission: `V6_EXTERNAL_EXCHANGE_V1`
Stop: **STOP C / CREDENTIAL_REQUIRED**
Level: **0**
Candidate: **0**
Four Xavier: **not started** (no exchange bytes)
Spent: **$0**
Final OOS: **not read**
`order_send`: **not called**

## What is true

Broker CFD information set is exhausted (V5.1). The missing object is exchange-derived structure, not another Ava OHLC variant.

Live Databento check 2026-08-29:

| Item | Fact |
| --- | --- |
| Dataset | `GLBX.MDP3` |
| Venues | CME, CBOT, NYMEX, COMEX |
| Asset class | Futures and options-on-futures |
| Dataset start | **2010-06-06 UTC** |
| `ohlcv-1d` / `definition` / `statistics` | from 2010-06-06 |
| `mbo` | from 2017-05-21 — not first pass |
| Historical billing | usage-based $/GB; **no monthly plan required** |
| Credits | **$125**, 6 months, one set per team |
| Standard | **$199/month** — do not open |
| Exact pull USD | `metadata.get_cost` after API key |

Recommended pack: **E** = `GC.FUT` + `CL.FUT` parent `ohlcv-1d` + `definition` + `statistics`.

## Built (not an empty architecture)

- Catalog / requirements / ROI / A–E packs (machine JSON)
- HTTP adapter: quote → L0 fetch → normalize → knowledge time → qualify → immutable `tm-fut-*`
- Novelty guard vs `FAILED_ALPHA_DATABASE_V2`
- Curve features (front/second, slope, inversion, roll yield, OI change)
- TERM_STRUCTURE_V1 search-space hash `5ce2c888aa5530113d769dda8af3602fc45dd96b2db273a73e764f3bf15bb4d0` (parents unassigned until acquire)
- Human decision pack

## Not done (legal stop)

No Databento key in `.env`. No bytes. No READY_FOR_RESEARCH. No Xavier. No Candidate.

Human action: credits + key, then **key is in .env, continue V6 acquire.**

## Distance to 10%

Unchanged. Level 0. The 10% question is still: missing alpha vs missing information. Pack E is the first test of the second branch.
