# DATA_PURCHASE_CASE — Databento / curve / surface

Do not buy yet unless a human accepts this case. Cash on hand for data: $0.

## Which exact Alpha does paid data unlock?

Not “more daily bars of GOLD/EURUSD”. Ava already gave those.

Paid futures/options data unlocks objects MT5 Ava does **not** have:

1. **Curve / calendar spread** — same root, multiple expiries. Mechanism class: carry along the curve, not CFD spot residual.
2. **Option surface** — strike × expiry × call/put. Mechanism class: IV, skew, term structure. Public GVZ/OVX already failed as an index proxy (`IMPLIED_VOL`).
3. **Exchange OI / volume by expiry** — positioning that is not CFTC Friday COT (already killed).

## Why this is not more Ava OHLC

841 listings were CFDs. `GOLD_FUTURE` has `expiration=0`. `option_mode=0` everywhere. Buying another CFD feed of the same names does not change the information set.

## Coverage / history / cost (to confirm on the vendor page at purchase time)

| Item | Need | Status |
|---|---|---|
| Product | CME metals or energy **curve** or equity-index **options** | BLOCKED until key |
| History | ≥ 10y daily settlement by expiry, or ≥ 5y surface snapshots | unconfirmed until fetch |
| Cost | Databento credits were ~$125 trial / Standard ~$199 last check (V3 pack) | PAYMENT_REQUIRED |
| Mechanism | pre-register **one** family, ≤ 3 hyps, freeze hash before first bar | not started |
| Expected value | unknown; only justified if the object is curve or surface | not a CAGR claim |

## Hypothesis skeleton (not executable until data exists)

- Economic mechanism: risk premium along a listed curve, or skew as a priced state.
- Data source: Databento (or equivalent) after human key.
- Feature: locked curve slope or 25Δ skew. Not RSI.
- Target: next-bar open of a listed lead contract or GOLD CFD only if the curve is the *information*, not the trade toy.

## After the key exists

Fetch → validate → immutable `*-YYYYMMDD-000001` (never `20260825` / `20260828`) → qualify → contract → local test → four Xavier.

Do not rewrite this case into “download another 841 CFD names”.
