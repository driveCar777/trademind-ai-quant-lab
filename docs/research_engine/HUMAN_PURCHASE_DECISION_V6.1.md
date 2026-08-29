# HUMAN_PURCHASE_DECISION_V6.1

Checked: **2026-08-29**
Stop: **CREDENTIAL_REQUIRED**
Level: **0**
Candidate: **0**
Spent: **$0**
Cost probe: **NOT RUN** (no key to call `metadata.get_cost`)

```text
ENV_EXISTS = true
KEY_PRESENT = false
```

`secret_scan` = **PASS**

## What was checked (no values printed)

Repo `.env` exists (1059 bytes, last written **2026-07-13**). It is the old Xavier worker file (`MASTER_HOST`, `RABBITMQ_*`, …). It does **not** contain `TRADEMIND_DATABENTO_API_KEY` or `DATABENTO_API_KEY`. Process environment also does not have that name.

So the human gate is **not** actually lifted. Nothing was downloaded. Credits were not charged.

## What to do (do not paste the key into chat)

**Option A — append to the existing repo `.env` (do not replace the file):**

```text
TRADEMIND_DATABENTO_API_KEY=
```

Put the Databento key immediately after `=`. Save the file.

**Option B — preferred, keeps Xavier worker vars separate:**

Create `.env.local` next to `.env` (gitignored). One line:

```text
TRADEMIND_DATABENTO_API_KEY=
```

Then in Cursor say: **key is in .env.local, continue V6.1 acquire.**

Do not commit `.env` or `.env.local`. Do not paste the key here.

## After the line exists

The next step is automatic: `metadata.get_cost` for Pack E. If ≤ $125, acquire `GC.FUT`+`CL.FUT` parent `ohlcv-1d`+`definition`+`statistics` from 2010-06-06. If > $125, stop with the real dollar amount. No $199/month.
