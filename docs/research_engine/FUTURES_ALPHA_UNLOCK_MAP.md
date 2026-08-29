# FUTURES_ALPHA_UNLOCK_MAP

Date: 2026-08-29  
Parents: Databento `GLBX.MDP3` `GC.FUT` + `CL.FUT` outrights.  
Not Ava `GOLD` / `OIL`. Not vendor continuous.

| Information | Status | Notes |
|---|---|---|
| Official settlement curve (front / second) | TESTED | Panel `tm-fut-GLBX-CURVE-D1-20260829-000001` |
| Backwardation / contango / slope | TESTED FALSIFIED | HYP-TSFUT-0001 LEVEL_LEAK occ 0.55 |
| One-day steepening | TESTED FALSIFIED | HYP-TSFUT-0002 LEVEL_LEAK occ 0.68 |
| Front-second roll yield | TESTED FALSIFIED | HYP-TSFUT-0003 same days as 0001 |
| Cleared volume / open interest | AVAILABLE unused | Knowledge = T+1 21:00Z. Not in the 3 hyps. Do not open a 4th hyp to rescue. |
| Ava CFD as futures or spot | BLOCKED | |
| Options-on-futures / IV surface | BLOCKED | Next information. Quote first. |
| MBO / trades / BBO / tick | BLOCKED | First pass forbidden |
| CME Standard $199/mo | BLOCKED | Historical usage only |

If asked to continue: quote options-on-futures. Do not retune this curve family.
