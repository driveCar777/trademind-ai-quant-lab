# V14.1 Corporate Action Audit

Canonical ranking and PnL stay on **raw** prices. No frozen QFQ panel. Do not freeze a new panel. Do not buy data.

| | H11 | H12 |
|---|---|---|
| Filled names checked | 100278 | 98101 |
| close/preclose > 12% | 0 | 1 |
| Return type | PRICE_RETURN_RAW_OPEN_TO_OPEN | PRICE_RETURN_RAW_OPEN_TO_OPEN |
| Dividend | DIVIDEND_EXCLUSION | DIVIDEND_EXCLUSION |
| QFQ | DATA_GAP | DATA_GAP |

Current V14 is a **price return**, not a total return. Cash dividends never enter P&L.

CANDIDATE_REPRESENTATION_RISK is recorded because raw-close ranking and raw-open PnL ignore cash dividends, splits-as-adjusted, and rights. A frozen QFQ panel **might** change both the statistic and the book. That is not a license to switch the canonical object. QFQ remains DATA_GAP. $0. No Tushare / Wind / Choice.
