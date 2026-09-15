# A_SHORT_DATA_FLOW_V2.md

> Data Flow v2（Phase 1.1）。在 v1（`A_SHORT_DATA_FLOW.md`）基础上加：**Prediction/Recommendation/Execution 三层落点**、**Track A(D1)/Track B(intraday) 分离**、**Candidate Funnel = 资源预算不是 alpha 参数**、**LLM 历史回测 vs 实时纸面决策 的边界**。

---

## 1. 主链路（三层落点标注）

```
External → Raw → Normalize → PIT → Live Pack (T×N)
                                     │
          ┌──────────────────────────┴─────────────────────────┐
          │  Local Quant (数学事实)                              │
          │   Market State · Theme/Leader · Capital · Behavior   │
          │   短窗特征 → walk-forward → 截面分/期望收益/概率      │
          └───────────────┬──────────────────────────────────────┘
                          ▼   =====>  [1] PREDICTION  (P(T+1>+5%)=0.61)
          Candidate Generation  (资源预算漏斗, §15)
                          ▼
          LLM Intelligence (信息理解, 非可回测特征)
                          ▼
          Red-Team → Quant⊕LLM Fusion + 双可信度
                          ▼   =====>  [2] RECOMMENDATION (A/B/S, immutable)
          Portfolio Decision (capital/lot/T+1/相关/流动/涨跌停)
                          ▼   =====>  [3] PAPER EXECUTION (09:30 开盘价)
          Ledger → Outcome (predicted vs paper executable, §24)
```
三层不混算（§2）；详见 [Runtime v2](A_SHORT_RUNTIME_ARCHITECTURE_V2.md) §1。

---

## 2. Candidate Funnel = 资源预算，不是隐藏 alpha 参数（§15）

Phase 1 的 `5000→1200→200→50→20→10~15` **重新定义**为**计算/API 容量预算**，不是回测调出来的 alpha selection rule：

```
Universe        = 全部 eligible 股票（规则/流动性/ST/停牌/涨跌停/成本可行性）
Local budget N  ≤ 本地深度打分容量（资源约束）
LLM budget M    ≤ LLM 深度分析容量（token/$/latency 约束）
Red-team budget K ≤ 红队容量
```
- `N/M/K` 是**资源上限**，不得为「回测效果」调参；改 N/M/K 属于 Portfolio/资源层，不改 Alpha model。
- **必须记录每只被排除的原因**（`why_excluded`：below_score / illiquid / ST / suspended / cost_infeasible / budget_cut），进 Recommendation 快照可追溯（§43）。
- Alpha 分数由模型决定；漏斗只决定「谁进入更贵的下一层分析」，不改分数排序。

---

## 3. Track A / Track B 分离（§16）——分钟数据不阻塞启动

| | Track A（D1） | Track B（intraday M5/M1） |
|---|---|---|
| 目标 | **先验证是否存在可交易 short-horizon alpha**（T+1/T+2/T+3/T+5） | 先 **acquire + store + quality monitor + build history** |
| 数据 | 复用现有 D1 pack/PIT/成本/账本 | 新 `tm-ashare-…-M5-…` 采集，**不立即进生产 alpha** |
| 状态 | **立即可做**（Phase 2 起点） | 攒历史深度 + 质量，够了再开**独立研究合同** |
| 依赖 | 无（现有件足够） | BaoStock 分钟（深度未实测）；不阻塞 Track A |

**结论（§28.Research）**：**D1 short-horizon alpha 能先独立研究，不等分钟数据。** 分钟只做「采集+质量+攒库」的 Track B，不做整个 A-Short 的启动阻塞。

---

## 4. LLM：历史回测 vs 实时纸面决策（§9、§10）——修正 Phase 1 表述

Phase 1 说「LLM = operational gate」过严。修正为 **LLM = Information Intelligence + Decision Support**（Decision A-001）：

| 场景 | LLM 可否参与 | 规则 |
|------|--------------|------|
| **Historical Backtest** | **不可**当已完成的历史 alpha | 无历史 PIT news/policy corpus → 不得把实时 LLM 输出包装成历史回测特征（结构上不可回测：前视+检索时点不可复现） |
| **Realtime Shadow / Paper** | **可** | 当天真实获得的 news/policy/announcement/macro/global → LLM 做 information interpretation / event assessment / theme / contradiction / candidate review / recommendation fusion |
| 任意场景 | LLM **无交易权** | 最终 Paper 由 Local Decision / Portfolio Engine 控制；`LLM ≠ Alpha-only`，`LLM ≠ Trading Authority` |

**若未来要回测新闻/政策 alpha**（§10）：必须先建 **timestamped historical evidence corpus**，每条含：
```
published_time · captured_time · knowledge_time · source · content_hash
```
在该 corpus 建成前，LLM 只进实时 shadow/paper，不进历史回测统计闸。

---

## 5. 失败传播（对齐 §18/§19 语义）

- 核心（Price/Calendar/Universe）失败 → `DATA_FAILED` → `NO RECOMMENDATION`（不拿旧数据续）。
- 非核心（News/Policy/Macro/LLM）失败 → 降级 Quant-only，标 `DEGRADED`/`UNAVAILABLE`（非 0），`INFORMATION_CONFIDENCE=DEGRADED`。
- **失败态绝不伪装成 `NO_EDGE`**（§18）：`SYSTEM_FAILED/DATA_FAILED/LLM_PARTIAL/PIPELINE_FAILED` 显式呈现。
- 连续 10/20/30 日无交易 → Opportunity Suppression Audit → `TRUE_NO_EDGE / SYSTEM_TOO_STRICT / DATA_FAILURE / MODEL_FAILURE / PIPELINE_FAILURE`（§19）。

---

## 6. 数据复用（§17）——不建第二套 A 股数据系统

复用现有：calendar / universe / D1 price / PIT / raw storage / cache / source registry / fundamental / macro-global / margin / data-health 模式。
**仅 A-Short 真正新增的数据**（分钟、题材/龙头/龙虎榜/资金流、新闻/政策文本）才新增 adapter/table/pack，并登进统一 source registry（EXTEND，不造第四套）。
