# V7 Information Fusion Report

Mission: maximize already-owned MT5 + public + Databento GC/CL. No new purchase.

## Official answers

1. **Current Level?** 0
2. **Candidate?** 0
3. **已有数据资产有多少？** 110 frozen immutable datasets (107 FREE, 1 PAID curve, 2 DERIVED OI/volume panels) plus Pack E raw (60 files, gitignored).
4. **FREE / PAID / DERIVED?** FREE 107 (MT5 CFD + public alt). PAID 1 (slim GLBX curve from Pack E). DERIVED 2 (OI-flow, volume-flow). Pack E raw = PAID, preserved, not in Git.
5. **Databento credits 剩余多少？** ≈ **$93.18** estimate. This mission spent **$0**. API balance not re-queried (quote-first / no request).
6. **新产生了多少 INFORMATION FEATURES？** Catalogued and derived: OI change, price×OI (new_longs / short_cover / new_shorts), cleared volume, volume×price, days_to_expiry, front identity roll. Slope/roll already existed and stay killed. Third-contract/curvature still need a local rescan if ever wanted.
7. **新机制多少？** 3 new families, 9 hypotheses (OI 3 + volume 3 + DTE 3). Not a reopen of V0.8.
8. **失败多少？** 3/3 families. OI and volume NO_CANDIDATE. DTE WEAK_EDGE (1 book-pass, FDR 0/3).
9. **Candidate多少？** 0
10. **如果没有：为什么？** Official OI×price is not rare enough / not confirmed out of sample. Volume×price loses money after 2 bp. DTE/roll is sparse; only post-roll passed the book gate and failed FDR. Cost and holdout still kill the rest.
11. **距离长期10%最真实的障碍？** Missing **non-price information that is not already in the futures structure we tested**. 10% is a Level-2 strategy question. We do not have a Level-1 Candidate, so CAGR is not evaluable without fabricating leverage.
12. **下一美元是否值得花？** Only after a **quote**. Not automatically. Remaining credits are for a new schema (options), not a second copy of Pack E.
13. **如果需要：买什么？多少钱？为什么？** Options-on-futures on GC/CL. Price unknown until `get_cost`. Why: no IV/skew/term in current bytes; GVZ/OVX already killed. Do not buy ORATS / CME DataMine / Trading Economics / $199 Standard in this gate.

## What was not done

- No new Databento historical job.
- No threshold rescue.
- No Final OOS.
- No `order_send`.
- No strategy layer (no Candidate).
- Unused $0 fusions (OI vs COT, CL+EIA) left unrun on purpose: they glue killed legs.

## Cross-checks

| family | hash | 01==04 |
|---|---|---|
| FUTURES_OI_FLOW_V1 | `8ff94bd0…abbbc` | `a97230b2…e4ecfe` |
| VOLUME_PRICE_FLOW_V1 | `e2e78ae9…c70f0` | `673721b7…5057c` |
| DTE_ROLL_WINDOW_V1 | `7b7451ab…4f365` | `c51ea761…1c738` |
