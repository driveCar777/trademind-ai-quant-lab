# TIME_STRUCTURE_V1 CONTRACT

Tag: `RESEARCH-2026-0002`

Not Institutional Time. Not weekday. Not a month-end window change.

search_space_hash: `51bb3eedac31936667271df8324df7e76b898a3b126a718b256e37591d7a93d2`

## Mechanism

Session-open inventory reprice at London cash open and New York FX cash open.

## Parents (new IDs only)

- `tm-market-GOLD-H1-20260828-000001` sha256 `d59c01d6a213066b409c6c8abeb85d1f4420bb5436541cf88af9112595e84496` (~7.715y)
- `tm-market-OIL-H1-20260828-000001` sha256 `dbdb5a29b7b36fd9db8fe631e41e818716ba08c9d5d207009e833f8ba51944c8` (~7.715y)

Do not use `*-20260825-*` short H1 packs.

## Events (worker cannot invent Tokyo)

- `LONDON_OPEN_H1`: 08:00 Europe/London. UTC hour 8 winter / 7 summer. EU last-Sunday March/October table.
- `NY_FX_OPEN_H1`: 08:00 America/New_York. UTC hour 13 winter / 12 summer. US 2nd-Sunday March / 1st-Sunday November table.

DST tables are date-only. No prices.

## Hypotheses

| ID | Event | Target | Sign |
| --- | --- | --- | --- |
| HYP-TS-0001 | London open H1 | GOLD | + |
| HYP-TS-0002 | London open H1 | OIL | + |
| HYP-TS-0003 | NY FX open H1 | GOLD | + |

hold=5 H1 bars. NEXT_BAR_OPEN. V0.6 cost. risk 0.5% 1x. seed 20260828. 70/15/15. FDR m=3 q=0.05. Final OOS DENIED.

## Failure

Do not add Tokyo. Do not switch to weekday. Do not change hold. Do not reopen Institutional Time month-end.
