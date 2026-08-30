# Options IV Model Limitations V8.3

Also satisfies `IV_QUALITY_LIMITATIONS_V8_3`.

IV on GLBX OG/LO is **DERIVED**, not **EXCHANGE IV**. Databento `statistics` defines `stat_type` 14/15, but the GLBX.MDP3 dataset table does **not** publish them.

---

## Model

**Black-76** (futures option). Not equity Black-Scholes.

| Input | Source | Already owned? |
|-------|--------|----------------|
| Futures price F | Pack E GC/CL `front_settle` | YES — do not rebuy |
| Strike K | definition / raw symbol | NO — need options definition |
| Expiry T | definition.expiration | NO — exact time UNKNOWN until bytes |
| Option price | ohlcv-1d close (MVD-A) or statistics settle (MVD-B) | NO |
| Rate r | UST DGS10 | YES — proxy, not a matching curve |

Assumptions:

- European futures option. OG/LO are **American**. Early-exercise premium is ignored.
- One rate for all expiries.
- One F per session (front settle), even if the option’s designated underlying is the second future.

---

## Quality limits (MVD-A)

| Limit | Effect |
|-------|--------|
| No bid/ask | IV is last-trade, not mid-market. **RESEARCH_LIMITATION** |
| Possible stale prints | A single late trade can pin OHLC |
| Settlement mismatch | ohlcv close ≠ official settle (`stat_type=3` is statistics only) |
| Illiquid strikes | listed ≠ traded; OG futures-front ATM sample rate was 0/8 |
| Zero-volume | `ohlcv-1d` should omit the day; do not invent a price |
| American exercise | Black-76 residual, larger near expiry / deep ITM puts |
| Rate proxy | DGS10 is not the dollar discount curve for that expiry |
| Parent junk | UD spreads inflate definition/ohlcv parent counts |
| Sample ≠ census | 8 dates, not 252 |

---

## Dirty-observation gate (apply after any future purchase)

Reject before inversion if any of:

1. no ohlcv row that session  
2. `volume = 0`  
3. OHLC all equal and volume = 1 (one-tick)  
4. strike distance `abs(K−F)/F` outside the pre-registered bucket  
5. knowledge time not strictly before the target session  

Do not relax these after seeing PnL.

---

## What MVD-B would change

Official settlement + OI + cleared volume. Still no venue IV. Still no bid/ask surface. Still American + rate proxy. Not required to **attempt** DERIVED IV. Useful as a liquidity filter, not as a reason to skip occupancy.
