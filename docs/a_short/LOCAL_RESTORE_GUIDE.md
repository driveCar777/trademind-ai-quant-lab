# LOCAL_RESTORE_GUIDE.md

> 本地重新 clone 后如何恢复并验证 A-Short（`cn_a_short`）。只覆盖 A-Short 部分；不涉及 master/api、ai-gateway、worker 的完整启动。

---

## 0. 前提
- Python **3.8–3.12**（Cloud 用 3.12.3；仓库技术栈冻结 Python 3.8 兼容，`cn_a_short` 两者皆可）。
- `cn_a_short` 运行/测试**只需 `numpy`**（跑测试再加 `pytest`）。**不需要** baostock（那是数据采集用）。

## 1. 安装环境
```bash
git clone https://github.com/driveCar777/trademind-ai-quant-lab.git
cd trademind-ai-quant-lab
git checkout cursor/a-short-architecture-forensic-3072   # 或合并 PR #2 后的目标分支
python -m venv .venv-ashort        # 可选；.venv-*/ 已 gitignore
# Windows: .venv-ashort\Scripts\activate   |  *nix: source .venv-ashort/bin/activate
```

## 2. 恢复依赖
```bash
python -m pip install --upgrade pip
python -m pip install numpy pytest
```
> 无需 `requirements.txt`（A-Short 极简）。若要跑数据采集/其它模块，另按各自目录的 requirements 安装（不在本指南范围）。

## 3. 运行测试（业务不变量，非"跑通"）
```bash
python -m pytest research_engine/cn_a_short/tests/ -q
# 期望: 33 passed
```
覆盖：成本算术/最低佣金、一手、T+1、hold spacing、涨跌停、停牌、fee-aware affordability、true-cash 无负、forward label、Top-K 选择、PIT cutoff、capital-path exit-recovery（carry/STUCK）、panel_coverage 退化守卫。

## 4. 生成成本/账户报表（无需行情数据）
```bash
python -m research_engine.cn_a_short.report_tables
# WROTE data/market/research_engine/cn_a_short/PHASE2A_TABLES.json  (确定性，可复现)
```

## 5. 运行 empirical baseline（需冻结 D1 面板字节）
```bash
python -m research_engine.cn_a_short.run_baseline
```
- **有冻结 pack**（本地 D: 有 `raw/daily_panel_v12_1` 且 `pack_panel()` 已物化）→ 跑 20 主比较（4 horizon × 5 TopK），写 `PHASE2A2_RESULTS.json`。
- **无 pack** → 输出 `DATA_BLOCKED`（正常）；先解决数据（见 `A_SHORT_CLOUD_FINAL_AUDIT.md` G0）。
- 若面板存在但退化（全 NaN）→ 自动报 `DEGENERATE_PANEL_NO_PRICES`（守卫）。

## 6. 物化冻结 pack（仅在有原始字节的本地机）
```bash
python -c "from research_engine.cn_a_share_alpha.pack import pack_panel; pack_panel()"
python -c "from research_engine.cn_a_share_alpha.pack import pack_exists; print(pack_exists())"
```
> 需要 `data/market/cn_a_share/raw/daily_panel_v12_1/symbols/<symbol>/raw.csv`（约 124GB，gitignored，不在 git）。若本地也没有 → 见数据策略与解冻决策。

## 7. 常见问题
- `No module named numpy/pytest` → 执行第 2 步。
- `run_baseline` 返回 DATA_BLOCKED → 冻结面板未物化（预期；非 bug）。
- PEP 668「externally-managed」→ 用 venv，或 `pip install --break-system-packages`（Cloud 上用过）。
- 不要提交 `.venv-*/`、`data/.../raw`、`alpha_cache`、`PHASE2A2_*` 的时间戳 churn（见 `DATA_STORAGE_POLICY.md`）。
