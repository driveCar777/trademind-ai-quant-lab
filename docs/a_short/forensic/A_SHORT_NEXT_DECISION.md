# A_SHORT_NEXT_DECISION.md

> §7：Phase 2B 是否应该开始？如果不能，先补什么？（只给建议，不开发。）

---

## 决定
```
PHASE 2B: 现在不能开始（DO NOT START）
```
Phase 2B（新闻/政策/LLM/信息融合）依赖一条**尚未打通的前置链**。在最基础的 D1 数值 baseline 都因数据不可用而**从未跑过一次**、且当前信号只有 20D 动量、universe 天然偏垃圾股的情况下，接 LLM/新闻只会**用漂亮的信息层包装一个未验证、可能全是 β 的空壳**——这正是治理反复禁止的模式（"不能用 LLM 弥补没有 alpha"）。

## 为什么不能（阻塞项，按严重度）
1. **数据硬阻塞（最高）**：冻结 D1 面板字节在 Cloud 不可用（`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`，Phase 2A.3）。→ 连 Q1–Q7 都答不了。
2. **信号未定型**：唯一打分是 20D 动量，与"短线"方向不符；短线特征族 0 实现。
3. **β 错觉风险**：ALL universe + 无质量过滤 → Top-K 偏小盘/低价/垃圾股；任何收益须先扣小盘 β。
4. **信息层未接入且无字节**：财务/行业/预告等有代码但 Cloud manifest-only、且未接 A-Short；龙虎榜/资金流/新闻政策/分钟数据**代码都没有**。
5. **运行时缺口**：无 :9002 / GUI / 通知 / scheduler / live 账本（全文档）。

## 先补什么（有序前置，逐步做，不跳级）
```
G0  数据解冻（Owner 决策，见 2A.3 §12）
     - 选项1：把冻结 raw/pack 字节上传到 Cloud 可达位置（保 id+hash 不变）→ pack_panel 可物化
     - 选项2：授权重新采集 + 注册新数据集（新 id/hash + 合同修订）——属新合同
     └─ 未解冻前：所有 empirical 停在 DATA_BLOCKED

G1  首轮 empirical D1 baseline（Phase 2A.2，数据到位后）
     - 跑 20 主比较（4 horizon × 5 TopK），读 coverage / carry_rate / stuck_rate / FDR
     - 诚实判 NO_ALPHA / WEAK / INCONCLUSIVE；结果差就如实记，不救

G2  β / universe 诊断（数值，非改 V1）
     - 分离小盘/低价 β vs 短线 alpha；登记（不实现）V2 质量/流动性过滤假设
     - 明确 A-Short 是否需要短线特征族（reversal/gap/量能/换手）替代 20D 动量 → 新合同 A_SHORT_D1_V2

G3  短线数值特征层（新预注册合同，仍无 LLM/新闻）
     - 只用可 PIT 数值：短反转/隔夜跳空/量能/换手/波动/breadth/涨停计数
     - 每族独立预注册、跑完冻结、计 m、corr vs 动量/ML1

G4  信息层接入（结构化，非文本）——仅在 G1–G3 出现可交易边后
     - 复用现有 margin/holders/financial/industry/index/preann 适配器（需先有 bytes）
     - 每层新合同、LO 账本闸、corr 独立性

G5  Phase 2B（新闻/政策/LLM/热点/龙头/龙虎榜/资金流）
     - 仅当 G1–G4 证明存在成本后、可执行、非纯 β 的短线数值 edge 才启动
     - 新闻/政策回测须先建 timestamped PIT 语料；LLM = 信息智能+决策支持，无交易权

G6  运行时 / 产品（并行工程，非 alpha 前提）
     - :9002 后端（复制 paper_ops 骨架）→ GUI（PySide6，Decision A-002）→ 通知（后台 toast，Decision A-004）→ scheduler
     - 仅在有可交易名单后才有意义
```

## 判定矩阵
| 门 | 前置 | 现状 | 可进入 2B？ |
|----|------|------|:---:|
| G0 数据 | Owner 上传/授权 | **BLOCKED** | 否 |
| G1 empirical baseline | G0 | 未跑 | 否 |
| G2 β 诊断 | G1 | 未做 | 否 |
| G3 短线特征（V2） | G2 | 未做 | 否 |
| G4 信息层接入 | G3 + bytes | 未做 | 否 |
| **G5 = Phase 2B** | G1–G4 全过 | — | **否（数门之外）** |

## 给 Owner 的两个决策点
1. **数据**：是否上传冻结字节到 Cloud（保 lineage），或授权注册新数据集？——**这是唯一能解除总阻塞的动作。**
2. **方向**：A-Short 是否用**短线数值特征族**取代 20D 动量作为第一信号层（新 `A_SHORT_D1_V2` 合同）？还是先按 V1 动量跑完 empirical 再定？

## 硬纪律（本阶段/近期）
不开发新策略、不改 V1/冻结合同/ML1/V33/hash/execution、不调参、不换源、不采购、不接 LLM 救场、不宣称 alpha、不为可行性弱化问题。**Audit → Architecture → Gap** 完成，**在 G0（数据）解决前不推进实现**。
