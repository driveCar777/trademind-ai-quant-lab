# data/samples

本机研究用的样本。不是实时行情。

- 只放 utf-8 的 `.csv`
- 文件名 = `sample_id`（小写字母、数字、下划线、短横）
- 指标：`symbol,close`（15～500 根），默认 `eurusd.csv`
- 因子：`stock,date`，默认 `moutai.csv`
- 回测：`strategy,symbol,start`，默认 `xauusd.csv`

换样本：把合规 csv 放进本目录。`GET /api/v1/samples` 会列出。
