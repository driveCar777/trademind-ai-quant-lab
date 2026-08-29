# V5 Next Decision

```text
LEVEL = 0
LEVEL_1_CANDIDATE = 0
STRATEGY = 0
```

## Stop reason

`EXTERNAL_DATA_GATE` + `PAYMENT_REQUIRED` if a human buys curve / surface data.

Not because “no Candidate = project failed”. Level 0 is the current fact.

## Why not another MT5 family

After V5 Top 5 plus BREADTH_V1 plus SIZE_SPREAD_V1, remaining 841 mass is:

- equity/ETF CFD clones and suffixes
- theme indices isomorphic to IDX_ASYNC / breadth
- bond CFDs isomorphic to killed rates

That is not a new information set.

## Human action

Do **not** buy more Ava OHLC.

If buying: Databento credits for **a specific curve or option surface** that unlocks a pre-written mechanism. Key goes in `.env` as `TRADEMIND_DATABENTO_API_KEY`. Then Cursor resumes ACQUIRE → hash → qualify → contract. See `DATA_PURCHASE_CASE.md`.

## Forbidden

- Retune BREADTH / SIZE / Top 5
- Read Final OOS
- `order_send`
- Leverage to fake 10%
