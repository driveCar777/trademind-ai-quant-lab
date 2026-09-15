# A_SHORT_LLM_PIPELINE_SPEC.md

> LLM 管线设计（§34–38）。复用锚点：`master/api/app/service/paper_fusion.py`（两层 Grok：匿名价格过滤 + 联网理解、`enforce` 硬截断、`priced_in` 门、三时钟、`prompt_hash`、审计块）、`cursor_cloud.py`（Cursor Cloud Agents 传输）、`ai-gateway/*`（本地 Qwen / DeepSeek）。
> **红线：LLM 是信息理解 + operational gate，不是 Alpha、不是可回测特征、不产生年化承诺。**

---

## 1. 职责划分（§37 / §38）——不让 LLM 代替 Quant

| 层 | 负责 | 现有实现 |
|----|------|----------|
| **Local Quant Engine（数学事实）** | technical/momentum/reversal/volume/amount/turnover/volatility/breadth/涨停统计/条件概率/历史类比/相关/排名/期望收益/概率/OOS/bootstrap/permutation/FDR | `ml_v25/model.py`,`alpha_v2/books.py`,`statistics.py`,`opportunity/score_v2.py` |
| **LLM（信息理解）** | 新闻/政策/公告/产业链/主题语义/事件影响/矛盾证据/假设生成/候选解释 | `paper_fusion.py::layer_b_prompt`,`cursor_cloud.py` |

Quant 出**数字**，LLM 出**理解**；LLM **不**计算期望收益/概率（那是 Quant）。

---

## 2. 漏斗内的 LLM 位置（§35）——绝不吃全市场

```
5000+ → Local Quant → 1200 → Local Alpha → 200 → Candidate Set → 50
   → LLM Deep Analysis → 20 → Red Team → 10~15 → Final Fusion
```
**禁止**：`5000 股 + 全新闻 + 全 policy + 全特征 → 一次 API`（§35）。
LLM 每次只收「候选子集（≤50）+ 该子集相关证据」。

---

## 3. 角色（§36）——多专用角色，禁自由聊天，只用结构化 JSON + Evidence IDs

| 角色 | 输入 | 输出（JSON） |
|------|------|--------------|
| Event Analyst | 候选 + 事件证据 | `{symbol, event_type, impact, horizon, claim_class, evidence_ids}` |
| Policy Analyst | 候选 + 政策证据 | `{symbol, policy_chain, structural_vs_tradable, evidence_ids}` |
| Theme Analyst | 候选 + 板块/主题证据 | `{symbol, theme, leader_state, acceleration, evidence_ids}` |
| Candidate Analyst | 候选深度 | `{symbol, bull, bear, priced_in, claim_class, evidence_ids}` |
| Contrarian / Red Team | 上述汇总 | `{symbol, refutations[], keep|drop, reason, evidence_ids}` |
| Final Synthesizer | 全部 | `{symbol, action, info_confidence, contradictions[], evidence_ids}` |

- **角色之间不自由对话**；一律 `Structured JSON + Evidence IDs`（§36）。
- 复用 `layer_b_prompt` 的 JSON 契约骨架（`exposure_pct/regime/themes[]/names[]{action,reason,tag,source,claim_class,priced_in}/avoid[]/confidence/disclaimer`）。
- 复用 `enforce()` 硬规则截断：`priced_in=true` 的 BUY→丢弃 `PRICED_IN_NEXT_OPEN`，SELL→降 HOLD；`narrative` 类降权；`hold_all` 审计。

---

## 4. 三时钟纪律（复用 `clocks_block`）

```
local_asof = 本地日线/名单（通常 T-1）
web_now    = LLM 联网今天的新闻/报价（不是成交价）
fill_date  = 下一交易日开盘
```
三者不一致是**设计**（`conflict:"EXPECTED"`），不是故障。防止「买新闻价」。

---

## 5. 证据与日志（§34）——每次重要调用必存

```json
{ "request": "...", "response": "...", "model": "grok-4.6",
  "prompt_version": "sha1[:12]", "timestamp": "...",
  "input_hash": "...", "output_hash": "...",
  "evidence_ids": ["EV-..."], "token_usage": {...}, "latency_ms": 0,
  "run_id": "...", "role": "EventAnalyst" }
```
用网页/新闻时，每条证据存：
```json
{ "evidence_id":"EV-...", "url":"...", "title":"...", "source":"...",
  "published_time":"...", "captured_time":"...", "content_hash":"..." }
```
- 复用 `prompt_hash()`（prompt 改 = 新序列）、`FUSION_ANON_LOG.json`/`FUSION_PLAN_*.json`（计划/决策归档）、`agent_id/run_id/duration_ms`。
- **NEW/EXTEND**：逐分析师 prompt/response 持久化（现仅 60 条环形）；证据库（evidence_ids 可回溯，§43 追溯链的一环）。

---

## 6. 传输 / 模型选择（复用）

| 通道 | 用途 | 现有 |
|------|------|------|
| Cursor Cloud Agents | 联网理解/红队（`grok-4.6 xhigh`） | `cursor_cloud.py`（5×重试、SSL EOF 硬化、`_adopt_created` 防重复计费） |
| DeepSeek / 本地 Qwen | 无需联网的结构化归纳 | `ai-gateway/*`（token 统计） |

模型选择：GUI 下拉，**禁手输**，无 key 项 `available=false`（仿 gateway 目录）。

---

## 7. 降级与成本（§34、§28、§30）

- **降级**：LLM 超时/大量 `UNKNOWN` → `LLM_PARTIAL` → Quant-only，标 `INFORMATION_CONFIDENCE=DEGRADED`（不置 0，§28）。News 源失败同理。
- **成本控制**：现仅 `MAX_GROK_CALLS_PER_DAY=3` 调用次数上限。**NEW**：token/$ 账本（Cursor Cloud Agents 不返回 usage，需按调用计费 + 预算闸）；并发/预算在 Settings 配（§52）。

---

## 8. 双可信度（§56）

Fusion 输出至少 `Quant Confidence` 与 `Information Confidence` 分列，再加 `Data Completeness` / `Execution Feasibility`。LLM 只贡献 `Information Confidence`，不改 `Quant Confidence`。

---

## 9. 治理红线（必须 owner 批准，详见 GAPS_AND_RISKS）

1. **Decision 017 禁云端 LLM API 作推理引擎**，而 SPEC §14 + fusion desk 实际用 Cursor/DeepSeek → **未消解冲突**；A-Short 依赖云 LLM，须一次新的 Decision/Amendment。
2. **News/Policy 是 `DATA_BLOCKED` 研究特征**；联网 LLM「结构上不可回测」（前视 + 检索时点不可复现 + 权重内前视）。故 **A-Short 的 LLM 产出不得进 Candidate 统计闸、不得当 alpha 回测**，只作 operational gate（SPEC §29.12：Grok 允许角色 = Research/Hypothesis/News/Regime/Feature 助手；禁 LLM→BUY→order）。
3. 红队当前只是**文档仪式**（`red_team/contrarian` 代码=0）；A-Short 需把红队落成代码化角色 + 采纳/拒绝 ledger（模板：`PAPER_HOT_DESK_V3_GROK_CONSULT.md`）。
