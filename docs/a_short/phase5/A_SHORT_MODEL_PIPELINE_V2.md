# A_SHORT_MODEL_PIPELINE_V2.md

> 模型架构设计（V2）。**只设计，不实现。** Rule + ML + LLM 信息层；**LLM = 信息抽取/推理助手，不是 alpha 预测器、无交易权**（Decision A-001）。

---

## 总管线
```
Data (PIT) → Features (registry) → [Rule model] ⊕ [ML model] → PREDICTION
                                        ⊕
               [LLM information layer]（信息抽取/事件/矛盾，结构化 JSON + 证据）
                                        ↓
                             FUSION（透明加权 + 红队）→ RECOMMENDATION（immutable）
                                        ↓
                             Portfolio/Execution（Layer 4）→ LEDGER → OUTCOME
```

## 1. Rule model（先行，最透明）
- 用途：Layer 0 regime 门（exposure_scalar、NO-TRADE 日）、Layer 3 风险叠加、硬约束（T+1/涨跌停/停牌）。
- 形式：显式规则 + 阈值（预注册），无拟合搜参。
- 价值：可解释、可审计、抗过拟合；作为 ML 的护栏与消融对照。

## 2. ML model（数值因子融合，Phase C）
- 输入：Layer 2 数值因子（registry，可 PIT）。
- 形式：walk-forward、REFIT 周期固定、无未来泄漏（沿用 ML1 的 REFIT_240 纪律，但**独立于 ML1，不改 ML1**）。
- 输出：截面 `selection_score` / 概率 / rank（PREDICTION 层）。
- 约束：预注册特征集、跑完冻结、计多重性 m；打过 EW/size-bucket/动量三基准 + 净后成本 + OOS + FDR 才算增量。
- 复用工程骨架（`cn_a_share_ml_v25` 模式）**但新 namespace/新合同**。

## 3. LLM information layer（Phase D，最后）
- **角色（permitted）**：对当日真实 news/policy/公告/事件做**信息抽取 / 事件评估 / 主题理解 / 矛盾分析 / 候选复核**，输出**结构化 JSON + Evidence IDs**。
- **硬禁（prohibited）**：`LLM → real order`、把 LLM 当直接 alpha 预测器、silent autonomy、用 LLM 输出当历史回测特征（无 timestamped 语料前）。
- 传输层复用 `master/api/service/cursor_cloud.py`（Grok via Cursor Agents）/ `ai-gateway`（Qwen/DeepSeek），**新增 A-Short 接线**；prompt 版本化 + 证据持久化 + token/$ 预算（沿用 `paper_fusion` 的 `prompt_hash`/`MAX_GROK_CALLS_PER_DAY`）。
- 历史回测 vs 实时：无 PIT 语料 → 只进实时 shadow/paper；要回测须先建 timestamped 语料（DATA_REQUIREMENT §Alternative）。

## 4. Fusion（融合 + 红队）
- 透明加权：`expected_return / confidence / cost_adjusted_expectancy`（第一版不做大量手工权重）。
- 红队/逆否：代码化角色 + 采纳/拒绝 ledger（模板 `PAPER_HOT_DESK_V3_GROK_CONSULT.md`）。
- 双可信度：Quant Confidence vs Information Confidence（Phase 1.1）。
- 输出 RECOMMENDATION（immutable 快照）；资金规模只在下游 Execution 改可执行性，不改分数。

## 5. 独立性 / 反过拟合
- corr vs ML1 < 0.90 才算独立；size-neutralized excess；regime split；FDR（BH q=0.05）计所有预注册比较。
- forensic `runs/RUN_ID/` 全程记录；失败归类 DATA/MODEL/EXECUTION/COST/ENV。

## 6. 明确不做（当前/近期）
- 不把 ML/LLM 接进来"救"未验证的 baseline（Phase 4 决策）。
- 不改 ML1/V33/V25/V26/V33/V34/V38；不采购；不接实盘。
- LLM 在 Phase D 才进，且永无交易权。

## 顺序（对齐 ROADMAP）
Rule（Phase A/B 护栏）→ 数值 ML（Phase C）→ LLM 信息层（Phase D）→ Fusion（Phase D）→ Paper（Phase E）→ 人审（Phase F）。**先证明数值因子扣成本后有边，再引入 LLM。**
