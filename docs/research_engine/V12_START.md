# V12 START — China A-Share Point-in-Time Research Foundation

**Date:** 2026-08-30  
**Purchase:** NO  
**Subscription:** NO  
**Alpha:** NO  
**Backtest:** NO  
**Final OOS:** DENIED  

## Mission

Build a point-in-time A-share research universe that does not lie to itself via survivorship, bad adjustment, future filings, or a UTC calendar.

```
LEVEL = 0
CANDIDATE = 0
NEW_PURCHASE = FALSE
ALPHA_RESEARCH = FALSE
NEXT_PRIMARY_RESEARCH_PATH = CHINA_A_SHARE_RESEARCH_UNIVERSE
```

This is data foundation only. Ready does not mean alpha.

## Phases

1. V12_START
2. SOURCE_AUDIT
3. SCHEMA
4. DATA_FACTORY
5. UNIVERSE
6. CORPORATE_ACTION
7. PIT
8. QUALITY
9. READY_GATE
10. FINAL_DECISION

## Hard rules

- Do not buy Tushare / Wind / Choice / CSMAR
- Do not run RSI / momentum / value / ML / backtest
- If delisted history is unavailable: `SURVIVORSHIP_BIAS_RISK` and do not mark RESEARCH_READY
- Financials without `announcement_date` are not RESEARCH_READY
- Large raw files stay on D: and out of Git
