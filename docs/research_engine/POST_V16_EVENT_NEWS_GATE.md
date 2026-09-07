# Post-V16 Event / News Gate

2026-09-02. Audit only. No download. No purchase.

## Event

`DATA_BLOCKED`

- `data/market/cn_a_share/announcements/` contains only `.gitkeep`
- V16: "Event layer still BLOCKED (no free PIT announcements)"
- No free point-in-time announcement / earnings-surprise / dividend-event panel is frozen
- Existing corporate-action file is a 600519 sample, not a panel
- BaoStock `query_dividend_data` was probed, not frozen. A live top-up would be a new download, not authorized here
- V13–V16 already use listing / ST / suspend as **eligibility**, not as an event-alpha

Cannot construct a pre-registered event family without inventing timestamps.

## News

`DATA_BLOCKED`

- Zero news files under `data/`
- `SRC-NEWS` remains blocked in the data-source registry
- No purchase of news API / Wind / Choice / CSMAR

## Next

Do not stop the mission on this gate. Continue to Alternative Information that can be built from the **already frozen** basics + `isST` + `tradestatus` + CN calendar.
