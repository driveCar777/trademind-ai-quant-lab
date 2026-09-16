# A_SHORT_RESEARCH_ROADMAP_V2.md

> V2 研究路线（阶段化）。**只设计，不实现。** 每阶段有明确前置门（gate），不跳级；每阶段产出 `runs/RUN_ID/` + 失败分类。

---

## Phase A — Data Foundation（数据地基）
- 目标：解除 **D1 pack 阻塞**（owner 决策，保 id+hash 或注册新数据集）；补齐最小地板（D1/日历/universe/指数日线 300·500·1000）。
- 产物：可物化 pack + `DATA_SNAPSHOT`（board/ST/价格/成交额/换手分层）。
- **Gate A**：`pack_exists()=True` 且覆盖率非退化；否则停在 DATA_BLOCKED（Phase 4 现状）。

## Phase B — Baseline Factors（数值因子 baseline）
- 目标：在真实 D1 上跑 `A_SHORT_D1_V1`（20D 动量 CONTROL）+ 逐个预注册 Layer 2 数值因子（registry），T+1..T+5 × Top3/5/10/20。
- 评估：IC/RankIC/胜率/收益分布 + 三基准（EW-eligible / size-bucket EW / 20D 动量）+ 净后成本 + attribution（β vs excess）+ regime split + FDR。
- **Gate B**：至少一个因子在**净后成本 + size-neutralized + OOS** 下显著打过三基准；否则记 FAILURE_ATLAS，不进 C。

## Phase C — Multi-factor Model（多因子/ML）
- 目标：把通过 Gate B 的因子组进 walk-forward ML（新 namespace/合同，独立于 ML1）。
- 评估：增量 vs 单因子、corr vs ML1 < 0.90、多重性、稳定性、capacity。
- **Gate C**：组合在验证+OOS 下有净后增量且独立；否则停。

## Phase D — Information Fusion（信息/LLM 融合）
- 目标：接结构化信息层（财务/行业/预告/资金流/龙虎榜——需数据）+ LLM 信息抽取（Decision A-001，无交易权）。
- 前置：Phase B/C 已证明数值边；新闻/政策须先建 timestamped PIT 语料才可回测。
- **Gate D**：信息层带来独立增量（corr < 0.90，净后正），否则只作实时 shadow 不进统计闸。

## Phase E — Paper Trading（纸面）
- 目标：复用 `paper_ops` 骨架 → A-Short `:9002` 后端 + 影子账本 + 每日短名单；后台通知（Decision A-004）。
- 前置：有可交易名单（Gate B/C/D 至少一个可部署袖）。**PAPER ONLY / LONG ONLY / 无 order_send。**
- **Gate E**：影子账本前向≥N 期结算后再读；不承诺收益。

## Phase F — Human Review（人审）
- 目标：owner 审阅前向证据（forensic REPORT）+ 决定是否上模拟盘/继续。
- 纪律：不为收益改规则；坏消息优先；任何"高收益"先加大审计（leakage/幸存者/β/重复检验/regime）。

---

## 阶段门总览
| 阶段 | 前置 gate | 现状 |
|------|-----------|------|
| A 数据 | owner 解冻数据 | **BLOCKED** |
| B baseline 因子 | Gate A | 未开始（引擎就绪） |
| C 多因子 | Gate B（净后有边） | 未开始 |
| D 信息/LLM | Gate C + PIT 语料 | 未开始 |
| E 纸面 | 有可部署袖 | 未开始 |
| F 人审 | Gate E | 未开始 |

## 硬纪律（全程）
不改冻结物/合同/参数/universe（除非新预注册合同）；不采购/不换源/不改 hash；LLM 无交易权、不当 alpha；不接实盘；每阶段 `runs/RUN_ID/` + 失败分类；**先证据后复杂度**。当前总阻塞 = Phase A 数据（Phase 4 STOP）。
