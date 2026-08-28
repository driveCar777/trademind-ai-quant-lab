# TIME_STRUCTURE_V1 — executed and killed

Tag: `RESEARCH-2026-0002`

search_space_hash: `51bb3eedac31936667271df8324df7e76b898a3b126a718b256e37591d7a93d2`

Parents: GOLD/OIL H1 `20260828-000001` (~7.715y). Not the short 20260825 H1 packs.

## Program

**NO_CANDIDATE**. All three **FALSIFIED**. Candidate = 0.

Occupancy ≈ 4.37% (session hour, not a level). n_trade research ≈ 1394.

Long session-open + hold 5h + V0.6 cost lost money on GOLD and OIL in research and validation. Predicted sign was +. Observed sign was −. Do not flip the sign.

HYP-TS-0003 raw_p = 0.0035 on local-full is a delta-vs-baseline number, not a profitable book. TR still ≈ −96% research. Not a Candidate.

## Kill

Family `FAM-TS-SESSION-0001` is **KILLED**.

Forbidden reopen:

- add Tokyo / Asia open to this family
- weekday dummy
- flip sign after seeing PnL
- change hold
- reopen Institutional Time month-end

## Next

`MICROSTRUCTURE_SURPRISE_V1` — tick_volume **surprise vs same-hour baseline**, not the killed FD tickvol **level**.
