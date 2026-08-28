# HUMAN_REQUIRED_ACTIONS — Data Expansion V3.0

Cursor cannot finish the next information source. The remaining high-value eyes need an account, a key, or a payment.

Do these in order. Do not buy all of them.

---

## ACTION-001 — Buy / open Databento (recommended)

**购买什么:** Databento account + $125 new-user credits. First pull: CME GC and CL **individual contracts** daily OHLCV + definitions + statistics (volume / open interest). Not a continuous adjusted series.

**在哪购买:** https://databento.com/signup then https://databento.com/pricing

**预计费用:** $0 cash if credits cover the first historical pull. Credits expire in 6 months. CME Standard is **$199/month** if you later need a live/unlimited plan (rate as of 2026-06-22). Do not start Standard until credits prove the files are usable.

**购买后拿到什么:** API key. Historical binaries/CSV for GC/CL contracts.

**放在哪里:**

1. Put the key only in local `.env` as `TRADEMIND_DATABENTO_API_KEY=`
2. Never commit `.env`
3. Raw files go under `data/market/immutable/` with a **new** `dataset_id` after Cursor hashes them
4. Git keeps manifest + sha256 only

**如何配置:** Copy `.env.example` → `.env`. Fill `TRADEMIND_DATABENTO_API_KEY`. Keep Clash on if that is how this machine reaches the API.

**Cursor 之后自动做什么:**

1. Fetch GC/CL all contracts (daily) via the adapter
2. Normalize to `futures_contract` schema
3. Qualify timestamps / duplicates / OI / lookahead
4. If PASS → `READY_FOR_RESEARCH`
5. Write `ALPHA_UNLOCK_MAP_DATABENTO_CURVE.md`
6. Open **one** new family, max 3 hypotheses (roll / basis / backwardation)
7. Local leakage + deterministic tests
8. Four Xavier (01–03 PRIMARY, 04 CROSS CHECK)
9. Candidate gate or KILL then next source (ORATS)

---

## ACTION-002 — Do not buy yet: ORATS

**购买什么:** Near-EOD historical archive.

**在哪购买:** https://orats.com/near-eod-data

**预计费用:** **$599** one-time. Recurring **$99/month** only if we keep the surface live after hist is hashed.

**为什么现在不买:** Databento credits are cheaper and open a mechanism Ava physically cannot see (contract curve). ORATS is ETF options (GLD/USO), not XAU/WTI listed. Still valid **after** curve is tested or if Databento is refused.

**买完以后:** Same factory: qualify → unlock → max 3 hyps → Xavier. Stop renewing $99/mo after 3 families NO_CANDIDATE.

---

## ACTION-003 — Backup curve: FirstRate GC/CL individual contracts

**在哪购买:** https://firstratedata.com/i/futures/GC and `/CL`

**预计费用:** Listed individual ticker **$99.95** (2024 list; confirm 2026 cart). Sample download is **PROBE**, not PRODUCTION.

**只用未调整的单合约文件。** Adjusted continuous is not a futures curve for this mission.

---

## ACTION-004 — Do not buy first: Trading Economics / CME DataMine

Consensus calendar: about **$149–$199/mo**. Official pricing page returned **403** from this host on 2026-08-28. TE Forecast may not be Bloomberg consensus. No first-print vintage ⇒ `DATA_BLOCKED_FOR_LIVE_RESEARCH`.

CME DataMine EOD: **$105–$2100/mo** by package (CME FAQ). Login + license. Worse friction than Databento credits for the same economic object.

---

## ACTION-005 — After any purchase

Tell Cursor: “key is in `.env`, continue Mission V3 acquire.”

Cursor will not invent READY_FOR_RESEARCH. If the pull fails license or schema, status stays DATA_BLOCKED.
