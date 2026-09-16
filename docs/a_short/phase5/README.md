# A-Short Phase 5 — V2 Research Platform Audit + Design

> **Audit + Design only. No code, no strategy, no trading.** 目标不是让 20D 动量赚钱，而是设计一个真正的 A 股短线（T+1~T+5、只多、纸面、无自动下单）研究平台，回答"扣除成本/流动性/涨跌停/T+1/执行约束后，是否存在稳定短线 alpha"。
> 硬约束：不改 ML1/V25/V26/V33/V34/V38 冻结物、不改现有合同、不宣称 alpha、不调参凑回测、不因结果差加过滤、不换冻结数据、不用 BaoStock 替代、不造假数据、不把 LLM 当 alpha 生成器、不接实盘。

---

## 文档
| 文件 | 内容 |
|------|------|
| [A_SHORT_V2_REQUIREMENT_MAPPING.md](A_SHORT_V2_REQUIREMENT_MAPPING.md) | 原始需求（热点/龙头/涨停/政策/央行/美联储/海外/汇率/商品/北向/资金流/龙虎榜/公告/财报…）× 已有能力 × 缺失 × 所需数据 |
| [A_SHORT_SIGNAL_ARCHITECTURE_V2.md](A_SHORT_SIGNAL_ARCHITECTURE_V2.md) | 5 层信号管线（Regime→Theme→Selection→Risk→Execution）+ Prediction/Recommendation/Execution/Ledger/Outcome |
| [A_SHORT_DATA_REQUIREMENT_V2.md](A_SHORT_DATA_REQUIREMENT_V2.md) | 所需数据集（source/frequency/history/PIT/storage）+ 现状对照 |
| [A_SHORT_FEATURE_REGISTRY_V2.md](A_SHORT_FEATURE_REGISTRY_V2.md) | 特征登记表（feature_id/name/category/formula/frequency/PIT/risk），仅登记不实现 |
| [A_SHORT_MODEL_PIPELINE_V2.md](A_SHORT_MODEL_PIPELINE_V2.md) | 模型架构（Rule + ML + LLM 信息层；LLM = 信息抽取/推理，不是 alpha 预测器） |
| [A_SHORT_RESEARCH_ROADMAP_V2.md](A_SHORT_RESEARCH_ROADMAP_V2.md) | 阶段 A 数据地基 → B baseline 因子 → C 多因子 → D 信息融合 → E 纸面 → F 人审 |

每次未来实验仍须产出 `runs/RUN_ID/`（manifest/dataset/universe/signal/trade/cost/attribution/report），失败必归类 DATA/MODEL/EXECUTION/COST/ENV_FAILURE（Phase 3 forensic 层已实现）。

---

## 六个关键问题（先答，再谈实现）

### 1. 是否放弃 20D 动量作为 baseline？
**不放弃——但把它降级为"对照/零假设"，不是策略。** 理由（非情绪）：
- 它**从未在真实数据上跑过**（Cloud DATA_BLOCKED），既不能说"有效"也不能说"无效"——放弃它等于放弃一个可复现、可解释、已被 forensic 观测的**基准系**。
- 研究价值在于**它是 β 探针**：任何 V2 因子必须同时打过「EW-eligible」**和**「size-bucket EW」**和**「20D 动量」三条基准，才算增量 selection alpha（见 Q5）。
- 结论：`A_SHORT_D1_V1`（20D 动量）保留为 **CONTROL baseline**；V2 因子登记为新合同，须证明相对它的增量。**不因为"看起来不赚钱"就删它。**

### 2. Phase 5 实现前的最小数据集？
**地板 = 冻结 D1 OHLCV pack（当前总阻塞）+ 交易日历 + PIT universe + 指数日线（HS300/500/1000）。**
- 有这四样即可跑：baseline（价格因子）、Layer 0 regime（指数趋势/波动）、按 size/流动性分层的 attribution。
- **没有 D1 pack 字节 → 一切 empirical 免谈**（Phase 4 STOP）。北向/资金流/龙虎榜/新闻/政策/分钟是**后续层**，不是 Phase 5 实现的前置。
- 详见 `A_SHORT_DATA_REQUIREMENT_V2.md §最小地板`。

### 3. Universe 从哪起（A 全部 / B 主板 / C 流动性过滤 / D 指数成分）？
**研究从 A（全 A 股，PIT），但强制分层评估 + 定义"可执行子宇宙"作为报告叠加，绝不把过滤写进 baseline。**
| 选项 | 优点 | 缺点 |
|------|------|------|
| A 全部 | 最大机会集、能测全 β、能**看见**垃圾股效应 | 含垃圾股/流动性陷阱，可成交性被高估 |
| B 主板 | 更干净、贴近用户权限 | 丢创业/科创短线机会 |
| C 流动性过滤 | 更可成交 | **过滤=隐藏问题**；且属"加过滤"（本阶段禁） |
| D 指数成分 | 干净、可成交、可对基准 | 机会集小、改变游戏（成分股非短线主战场） |
**推荐**：baseline 在 A 上跑；forensic `DATA_SNAPSHOT` 按 board/size/流动性/价格**分层报告**；另定义 `EXECUTABLE_SUBUNIVERSE`（ADV/价格门）**仅作报告叠加**，让"去掉垃圾股后还剩多少 alpha"可见——**不改 V1 universe**。V2 可预注册"可执行子宇宙"为新合同（Q4）。

### 4. 如何避免"回测靠垃圾股"？
**用 forensic 量化并暴露，而不是用过滤掩盖：**
1. `DATA_SNAPSHOT` 出 board/ST/价格/成交额/换手分位 → 看 Top-K 是否富集低价/微盘。
2. `attribution` 出 market_beta vs excess，size 分桶对照 → 量化"多少是小盘 β"。
3. **净后成本 + 流动性叠加**：垃圾股在 ¥5 最低佣金 + 冲击成本下常自灭；报告 net-after-cost 与 ADV-aware 可执行性。
4. 评估须同时对照「EW-eligible」+「size-bucket EW」+「20D 动量」（Q5）。
**禁**：因为出现垃圾股就加价格/市值过滤（本阶段禁；只能登记 V2 假设）。

### 5. 如何区分 真 alpha / 小盘 β / regime？
- **size-neutralized excess**：在 size 分桶内评估超额；对 market/size/momentum 做简单回归取残差。
- 三重基准：EW-eligible、size-matched EW、20D 动量；只有**同时打过三者 + 净后成本 + OOS + FDR** 的 selection 才算 alpha。
- **regime split**（Layer 0）：牛/熊/震荡、指数波动高低分段报告，避免"整段小盘牛"冒充 alpha。
- forensic `primary_conclusion` 已内置 `STYLE_EXPOSURE_ONLY`（超额 t 不显著但毛正 → β）。

### 6. LLM 何时进入？
**Phase D（信息融合），且在 Phase B/C 的数值因子证明"扣成本后有边"之后。**
- LLM = **信息抽取 + 推理助手**（对当日真实 news/policy/公告做结构化理解、事件评估、矛盾分析、候选复核），**不是** alpha 预测器、无交易权（Decision A-001）。
- 历史回测 LLM/新闻前，**必须先建 timestamped PIT 语料**（published/captured/knowledge_time/source/content_hash）；否则只进实时 shadow/paper，不进历史统计闸。
- 过早接 LLM = 在未验证地基上叠复杂度（Phase 4 决策已禁进 V2）。

---

## STATUS
Phase 5 = 文档交付（Audit + Design）。empirical 仍 **DATA_BLOCKED**（Phase 4），实现前须 owner 解冻数据。**STOP after documentation。**
