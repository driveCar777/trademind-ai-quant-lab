# TradeMind · A股纸面操作台（桌面 GUI）

A standalone **desktop** front-end (PySide6 / Qt6) for the existing **frozen**
A-share ML1 paper-trading pipeline. It is deliberately separate from the MT5 /
macro side and from the web dashboard.

> **只读 · 不发单。** This app never modifies models, never fetches the network,
> never places orders. It renders the artifacts produced by the research
> pipeline (`STATUS.json` / `SHORTLIST_*.json` / `LEDGER*.json`).

## Pages

| 页面 | 内容 |
|------|------|
| 今日操作台 | 本期持仓状态、操作规则、练手本金/预计投入、纪律横幅 |
| 短名单 | 前 N 只名单（排名 / 代码 / 模型分数条 / 最新价 / 手数 / 预计金额） |
| 持仓 · 账本 | 影子权益、周期表（信号日/建仓/预计平仓/成交/状态） |
| 运行健康 | 冻结数据集、哈希、股票数/交易日、增量步骤、数据目录 |

Look & feel: dark "cockpit" theme, animated sidebar highlight, KPI count-up,
fade/rise page transitions, pulsing live dot. A-share colour convention (红涨绿跌).

## Run (Windows, x86_64)

Requires Python 3.10+.

```bat
run.bat
```

`run.bat` creates a local `.venv`, installs `PySide6`, and launches the app.
Or manually:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m ashare_desktop
```

### Package to a single .exe (optional)

```bat
.venv\Scripts\python -m pip install pyinstaller
.venv\Scripts\pyinstaller --noconsole --name TradeMind-Ashare -F -m ashare_desktop
```

## Data location

By default it reads `data/market/cn_a_share/live/` from the repo root. Override
with the environment variable `TRADEMIND_ASHARE_LIVE` pointing at a `live/`
directory (containing `STATUS.json`, `signals/`, `ledger/`). If files are
missing, the UI degrades gracefully and the health page shows "数据缺失".

## Discipline (matches AGENTS.md)

- Front-end over the **frozen** ML1 / V26.x shell — no model, threshold, exit
  rule, or hold-period changes.
- `ORDER_SEND` is **not** wired anywhere. Execution stays manual by the owner.
- Shadow ledger only (`money = NONE`).
