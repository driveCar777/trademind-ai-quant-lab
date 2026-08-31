# V14.1 Cost Forensics

Locked model: commission 2.5bp, transfer 0.1bp, slippage 10bp, stamp 10bp sell before 2023-08-28 / 5bp after. Not MT5.

| | H11 | H12 |
|---|---|---|
| Gross | 337127.54 | 403670.27 |
| Fees (comm+transfer+stamp) | 215500.51 | 222850.09 |
| Slippage | 287424.14 | 297314.31 |
| Stamp | 140770.23 | 145548.37 |
| Net | -165797.11 | -116494.13 |
| Unfilled fees | 0.0 | 0.0 |
| Double charge | False | False |
| V13-style mean | 0.0868% | 0.1108% |
| Capital mean | 0.1155% | 0.1439% |
| Formula gap (cap − V13) | 0.0287% | 0.0330% |

Identity `net = gross - fees - slip` holds (H11 abs 5.326000973582268e-09).

Costs are charged once at entry and once at exit, only on fills. Unfilled orders produce no cost.

The Candidate subtracts one RT from the mean raw. The Strategy applies buy/sell factors on notional. That is a **formula difference**, not a double subtraction of the same book. FORENSIC_ERROR for double charge: **no**.

Cost does **not** flip a large positive Candidate into a large negative book. Capital-period means are slightly *better* than V13-style means. The sign flip is overlap + compounding.
