# A-share alpha V1 contract

Locked before ranking.

contract_hash = `b48b2657c4991041fb4e8f9fafa33c53c40be29222a1b39f87d24a82f596f75e`

| Item | Value |
|------|--------|
| dataset_id | `tm-ashare-EQUITY-D1-20260830-000002` |
| lookbacks | 20 / 60 / 120 |
| hold | 20 trading days |
| quantile | top/bottom 20% |
| capital book | LONG_ONLY equal-weight |
| long-short | research book only (no locate) |
| signal | raw close(t) |
| execution | raw open(t+1); limit/suspend/delist = NO_FILL |
| research | 2010-01-04 → 2021-08-24 |
| validation | 2021-08-25 → 2024-02-29 |
| denied | 2024-03-01 → 2026-08-28 |
| FDR | BH q=0.05 one-sided |
| seed | 20260831 |
| cost | A_SHARE_TRANSACTION_COST_MODEL_V1 |

Signs are locked. Do not flip after seeing results.
