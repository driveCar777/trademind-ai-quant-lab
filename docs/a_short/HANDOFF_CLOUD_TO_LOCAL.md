# HANDOFF_CLOUD_TO_LOCAL.md

> Cloud→Local 交接报告。**不夸大**：只写代码里真实存在的东西。

---

## 1. 当前项目真实状态

### Implemented（代码真实存在，Cloud 可测）
- `research_engine/cn_a_short/` 研究包（离线，仅依赖 numpy）
- **cost engine**：`cost.py`（逐笔佣金 min¥5 / 过户 / 印花 / 滑点，复用 canonical 常量）
- **account feasibility**：`account.py`（fee-aware 可执行性、最小资金、现金不为负）
- **baseline engine**：`baseline.py`（T+1..T+5 前向标签、Top-K 选择、撮合、成本、EW/动量对比、`panel_coverage` 守卫）
- **PIT / execution 正确性**：T+1、停牌/涨跌停/缺开盘、fee-aware 手数、capital-path exit-recovery（carry/STUCK）
- **paper execution skeleton**：`baseline.top_k_period`（离线撮合记账；**非** live 账本）
- **feasibility/report**：`feasibility.py`、`report_tables.py`（成本/账户表，无需 pack）
- **tests**：33 个单测（合成 pack），全绿
- **lineage/artifacts**：`run_baseline.py` 输出血缘元数据；DATA_BLOCKED 时写 `PHASE2A2_*` artifact

### Not implemented（明确未做，勿当"快好了"）
- 龙头识别 · 涨停策略 · 热点发现 · 板块轮动 · 龙虎榜 · 资金流
- 新闻 · 政策 · LLM 融合
- GUI · Windows 通知 · scheduler · `:9002` 后端 · live 账户
- 自动交易 / order_send / broker
- 短线数值特征族（reversal/gap/量能/换手/波动/breadth/涨停计数——仅 specified）
- 分钟/intraday 数据、任何信息层接入 A-Short

---

## 2. 当前研究状态
```
Contract:  A_SHORT_D1_V1
Status:    READY_FOR_DATA / NOT_ALPHA_PROVEN
Model:     20D_MOMENTUM_BASELINE  (baseline，不是最终策略)
Windows:   research 2014-01-01..2021-12-31 / validation 2022-01-01..2023-12-31 / OOS 2024-01-01.. (LOCKED)
Empirical: DATA_BLOCKED (Cloud 无冻结 D1 面板字节)
Tests:     33 passed
```
- **20D 动量只是 baseline 占位信号**，方向上甚至偏中周期，不是短线终版策略。
- **未证明任何 alpha**。Cloud 无法产出 empirical 结果。

---

## 3. 交接要点（给本地）
1. 全部成果已 push 到 `cursor/a-short-architecture-forensic-3072`（PR #2）。**Cloud VM 一次性，未 push 内容会丢。**
2. 本地 clone 后即可 `pytest` + `report_tables`（只需 numpy/pytest）；`run_baseline` 在有冻结 pack 的机器上才出 empirical。
3. 数据不随 git 走（见 `DATA_STORAGE_POLICY.md`）；解冻是 owner 决策（见 `A_SHORT_CLOUD_FINAL_AUDIT.md` G0）。
4. 恢复步骤见 `LOCAL_RESTORE_GUIDE.md`；本地恢复包见 `A_SHORT_LOCAL_HANDOFF.md`。
