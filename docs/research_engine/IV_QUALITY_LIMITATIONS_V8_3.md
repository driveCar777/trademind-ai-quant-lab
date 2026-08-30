# IV Quality Limitations V8.3

Canonical write-up: `OPTIONS_IV_MODEL_LIMITATIONS_V8_3.md`.

Short list:

- no bid/ask (MVD-A) → last-trade IV, not mid
- possible stale / one-tick prints
- American exercise vs Black-76
- DGS10 is a rate proxy
- ohlcv close ≠ official settlement
- illiquid strikes (listed ≠ priced)
- zero-volume days have no ohlcv-1d bar
- 8-date sample is not a 1Y census
- GLBX has no exchange IV
