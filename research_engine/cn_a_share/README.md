# China A-share data layer (V12)

Point-in-time research universe. **No alpha. No backtest. No purchase.**

```text
Windows Master downloads and validates.
Xavier is not required for this phase.
```

## Layout

- `schema.py` — daily / basic / financial columns, dataset IDs
- `calendar.py` — Asia/Shanghai trading calendar
- `universe.py` — listing window and as-of membership
- `bars.py` — raw prices never overwritten; qfq/hfq separate
- `corporate.py` — dividend + adjust-factor sample checks
- `pit.py` — knowledge-time and future-mutation tests
- `factory.py` — freeze versioned reference datasets
- `decision.py` — READY / CONDITIONAL / BLOCKED gate
- `compile.py` — reports under `docs/research_engine/`

Canonical source: BaoStock (no key). AkShare-class HTTP is cross-check only.

Large raw bars stay on `D:` under `data/market/cn_a_share/raw/` and are gitignored.
