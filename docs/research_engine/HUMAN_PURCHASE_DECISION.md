# HUMAN_PURCHASE_DECISION — V6

Checked: **2026-08-29**
Stop: **CREDENTIAL_REQUIRED**
Level: **0**  Candidate: **0**  Spent: **$0**

This is the only human gate. Catalog, ROI, pack E, adapter, knowledge-time, novelty, and TERM_STRUCTURE_V1 are already in the repo. The next byte cannot be fetched without a key.

## What to do

1. Open https://databento.com/signup
2. Keep the **$125** new-user credits (6 months, one set per team).
3. Do **not** start CME Standard **$199/month**.
4. Accept Databento + CME historical terms for internal research.
5. Put the key in repo `.env` as `TRADEMIND_DATABENTO_API_KEY=...`
6. In Cursor say: **key is in .env, continue V6 acquire.**

Do not paste the key into chat. Do not commit `.env`.

## Why this purchase

AvaTrade inventory is 841/841 CFD. True futures = 0. True options = 0. Every frozen family on that information set is Level 0.

Pack **E** is the minimum that is actually an exchange curve:

- dataset `GLBX.MDP3` (CME, CBOT, NYMEX, COMEX)
- parents `GC.FUT` + `CL.FUT`
- schemas `ohlcv-1d` + `definition` + `statistics`
- available from **2010-06-06** (live Availability details 2026-08-29)
- official settlement + open interest + expiry
- no ticks

`metadata.get_cost` runs first. If the quote is above $125, acquire stops and this file is rewritten with the number. No Standard subscription.

## If this works

TERM_STRUCTURE_V1 (3 pre-registered hypotheses) runs on the frozen panel. If a Level 1 Candidate appears: stop new alpha search.

## If curve fails

Do not retune slope, threshold, or hold. Next information = options-on-futures or macro surprise. Not RSI. Not another Ava variant.

## If get_cost > $125

Do not buy. Re-read this file. Compare D (drop definitions) only if the quote is still a one-time historical pull.
