# DATA_PURCHASE_ROI_V6

Checked: **2026-08-29** (live Databento pricing + `GLBX.MDP3` Availability details)

Rule: do not buy because the data looks advanced. Buy if it opens a **new economic mechanism** at the lowest cash.

Exact USD for a pull is **not** on the public page. It is `metadata.get_cost` after `TRADEMIND_DATABENTO_API_KEY`. Historical research does **not** require the $199 Standard plan.

| Source | Cost | History | New info | New mechanisms | Hyps | EV | Buy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Databento GC+CL L0 daily+def+stats | credits ≤ $125; quote after key | 2010-06-06 (16+ y claimed) | yes | 3 | 3 | high | **yes if get_cost ≤ 125** |
| Databento MBO/trades/BBO | large GB; MBO from 2017-05-21 | tick | yes | 0 now | 0 | low now | no |
| Databento Standard | $199/mo | 16+ y L0 | no vs PAYG hist | 0 | 0 | none for a one-shot curve | no |
| ORATS GLD/USO | $599 | 2007+ | yes | 1 later | 3 | high later | no, after curve |
| FirstRate GC/CL | ~$99.95/ticker | 2008+ | yes | 2 | 3 | medium backup | no |
| CME DataMine | $105–$2100/mo | official | yes | 3 | 3 | high, worse friction | no |

## Minimum packs A–E

| Pack | Content | Opens | Missing | Choose |
| --- | --- | --- | --- | --- |
| A | GC daily | thin GC shape | settle, OI, expiry, CL | no |
| B | CL daily | thin CL shape | settle, OI, expiry, GC | no |
| C | GC+CL daily | two roots, electronic close | official settle, OI, expiry | no |
| D | C + statistics | settle + OI | definitions | no unless E blows the cap |
| **E** | GC+CL daily + OI + definitions | term structure, OI+price, roll/basis | options, macro | **yes** |

Recommended: **E**. Fallback if `get_cost(E) > 125`: D then C. Never MBO. Never Standard to start.

Machine file: `data/market/research_engine/v6_external/DATA_PURCHASE_ROI_V6.json`
