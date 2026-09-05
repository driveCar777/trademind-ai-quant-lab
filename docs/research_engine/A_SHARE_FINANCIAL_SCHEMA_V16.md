# V16 Financial Schema

Normalized annual (Q4) rows from BaoStock `query_profit_data`.

| Field | Source | Notes |
|---|---|---|
| symbol | code | |
| report_period | statDate | Not knowledge time |
| announcement_date | pubDate | Knowledge time |
| revenue | MBRevenue | |
| net_profit | netProfit | |
| eps | epsTTM | **VENDOR_TTM**, not period EPS |
| roe | roeAvg | |
| roa | — | UNAVAILABLE |
| debt_ratio | liabilityToAsset | UNAVAILABLE unless balance downloaded |
| gross_margin | gpMargin | |
| np_margin | npMargin | |

RESTATEMENT_RISK: no version history.
Quarterly API exists; this freeze is annual Q4 only. TTM is not constructed from future quarters.
