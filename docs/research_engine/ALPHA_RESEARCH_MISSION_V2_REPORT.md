# Alpha Research Mission V2.0 Report

STOP: **B**

START_COMMIT: `48bc5e8d072c8942f7c6e92266bef91d3ca78a43`

END_COMMIT: `6365ade9e99eb4f193e79c0accf7f636605e51ce`

FINAL_OOS_TOUCHED: false

order_send: false

---

## Current Level

```text
LEVEL = 0
LEVEL_1_CANDIDATE = 0
STRATEGY = 0
PAPER = 0
MT5 = read-only / no order_send
```

CAGR >= 10% was not used as a discovery gate. There is still no Level 1 alpha, so there is no certified CAGR.

---

## What this mission changed

Previous missions exhausted **price / simple state / simple cross-asset / simple time / simple volume** on the Ava broker set.

This mission expanded the **information set** with public series that do not require an API key, subscription, or login:

| Source | Status | What it opened |
| --- | --- | --- |
| CBOE GVZ / OVX | ACQUIRED + TESTED | index-level IV / VRP shock, not a smile |
| CFTC disagg COT | ACQUIRED + TESTED | positioning extremes (Friday knowledge) |
| EIA WCESTUS1 | ACQUIRED + TESTED | US crude inventory shock |
| US Treasury 10y | ACQUIRED + TESTED | discount-rate shock on GOLD/OIL |
| NY Fed EFFR + ECB €STR + BOJ call | ACQUIRED + TESTED | overnight FX carry differential |

One source at a time. Max 3 hypotheses per family. z_cut was not widened after sparse occupancy.

---

## Executed families

| Family | Hash | Xavier | Outcome |
| --- | --- | --- | --- |
| IMPLIED_VOL_V1 | `f4bd4298a14eb0ac84cc7246319b4e3f323dc104583e5232902b8f289f5c3644` | 4, 01=04 | NO_CANDIDATE KILLED |
| POSITIONING_V1 | `4a1240f6059172baf283576aac082b0c62e0a0f56e5dae108e082dd76496caec` | 4, 01=04 | NO_CANDIDATE KILLED |
| INVENTORY_V1 | `944195090e6fb835aba35be30a7a13ffee437256b9ed3e5610b23fc7116b2c05` | 4, 01=04 | NO_CANDIDATE KILLED |
| RATES_V1 | `4bbbab85b281b6890b7b38342a82ea649fb56b6ac523b8a28cd6cac854fd54ef` | 4, 01=04 | NO_CANDIDATE KILLED |
| CARRY_V1 | `0ccbac180f72da54bcdca046922b13a7637e811da3bc85caed3f479d9018a7cb` | 4 | INVALID_ALIGNMENT (research window pre-€STR) |
| CARRY_V1A | `5974f11738baef21831a846991bd8d05dfa843e4c096e4f97ca636adcec03b46` | 4, 01=04 | NO_CANDIDATE KILLED |

Do not retune any of these. Do not flip signs. Do not change hold or z_cut.

---

## Tested alpha mechanisms (this mission)

1. **IV shock / VRP** — GVZ/OVX z-cross and GVZ minus GOLD RV20. Not V0.9 realized-vol ADX.
2. **Positioning washout / commercial crowding** — CFTC MM and commercial net/OI, Friday knowledge only.
3. **Inventory shock** — EIA crude stocks WoW z-cross on OIL; GOLD as a secondary draw test.
4. **Discount-rate shock** — UST 10y z-cross on GOLD/OIL. Not a yield-level always-on book.
5. **Overnight carry differential** — EFFR−€STR on EURUSD and EFFR−BOJ on USDJPY. Not V0.8 FX price → metal.

Closest non-candidate this mission: none worth promoting. Historical closest remains HYP-IT-0001 (Mission V1.1). Do not reopen.

---

## Failed directions

- Index IV z-cross and VRP rich-cross did not pass research+validation+FDR+two-target.
- Weekly COT extremes were too sparse for validation n>=4 after leak-free Friday knowledge. Do not lower z_cut.
- EIA inventory z-cross was sparse and not profitable.
- UST 10y z-cross on GOLD/OIL was not profitable / validation-thin.
- Overnight carry z-cross on EURUSD was **FALSIFIED** after cost (0001). USDJPY and the cheap side were INCONCLUSIVE, not a rescue target.

---

## Successful directions

None. No Level 1 Candidate. No Strategy Construction.

Data acquisition itself succeeded: eight new immutable alt datasets with manifests, SHA256, and knowledge-time rules.

---

## Data gaps (not pretend)

| Gap | Status | Required |
| --- | --- | --- |
| XAU/WTI option smile, skew, term structure | DATA_BLOCKED | paid vendor or broker option-chain history |
| Macro actual vs consensus (CPI/NFP/FOMC) | DATA_BLOCKED | consensus/whisper is paid. Actuals alone are not surprise |
| Commodity futures curve / roll yield | DATA_BLOCKED | Ava is CFD; no contract month or expiration |
| Gold ETF holdings / central-bank flows | DATA_BLOCKED | SPDR/WGC pages are HTML; no key-free structured history |
| News → structured event schema | DATA_BLOCKED | no schema yet; text→buy/sell forbidden |
| True 10y GOLD/OIL D1 | BROKER_LIMITATION | still 7.715y from 2018-12-12 |

---

## Distance to 10%

The obstacle is still **no Level 1 alpha**.

New public series did not produce a two-target, cost-adjusted, FDR q<0.05 edge. Therefore:

- Strategy Construction remains blocked
- Portfolio Construction remains blocked
- Certified CAGR remains undefined
- Leverage must not be used to manufacture 10%

---

## Next dollar

Not another z-cut on IV / COT / EIA / UST10 / overnight carry.

Legal remaining expansion requires **human / paid access**:

- option surface vendor
- consensus surprise vendor
- futures curve / exchange settlement history
- structured gold ETF / official sector flows

Until one of those arrives, this information-expansion loop is exhausted on the current machine.

---

## Stop rule

**STOP B:** every currently obtainable no-key public source that opened a new mechanism was acquired, qualified, contracted (max 3 hyps), executed on four Xavier, and killed or blocked.

Not STOP A (no Candidate).
Not STOP C (no secret/payment bypass was attempted; blocked sources are recorded, not scraped).
