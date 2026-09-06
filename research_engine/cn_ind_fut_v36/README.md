# cn_ind_fut_v36

A-share industry-bucket returns mapped onto China futures cross-section (V36). Contract: `docs/research_engine/V36_INDUSTRY_TO_FUTURES_CONTRACT.md`.

```
python -m research_engine.cn_ind_fut_v36.run
```

Refuses if `RESULTS.json` already exists. Labels / costs / LS tercile reuse V31 (`fwd_same`). Features are the five industry series only — not V31's price/OI/term set.
