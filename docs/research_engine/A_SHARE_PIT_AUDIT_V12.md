# A-share point-in-time audit V12

**Date:** 2026-08-30

## Knowledge-time 2024-01-01

- 茅台 2023 annual `pubDate=2024-04-03` is **not** visible on 2024-01-01.
- Visible financial rows as-of that date: 1
- Test ok: True

## Future mutation

- Future financial mutation stable: True
- Future price mutation stable: True
- Future IPO excluded from earlier universe: True
- `sh.600005` in universe 2016-12-30: True
- `sh.600005` out of universe 2017-03-01: True

## Industry

- Point-in-time industry: **NO**. LIMITATION. Do not backfill today's industry ten years.

## Financial research-ready

- Sample has `announcement_date`/`pubDate`. Full financial panel is **not** frozen. Not RESEARCH_READY.
