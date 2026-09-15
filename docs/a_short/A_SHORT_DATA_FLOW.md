# A_SHORT_DATA_FLOW.md

> External → Raw → PIT → Features → Candidates → LLM → Fusion → Recommendation → Paper → Outcome（§41）。
> 每一段标注：复用锚点、PIT 门、失败/降级行为。

---

## 1. 主链路（每日一次，尽量贴近 09:00 冻结）

```
External Data ──(增量)──▶ Raw Store ──(归一)──▶ PIT Gate ──▶ Live Pack (T×N)
                                                                   │
                 ┌─────────────────────────────────────────────────┘
                 ▼
        Market State / Regime      (breadth, 涨停数, 换手 z, trend/ADX/vol)
                 │
                 ▼
        Macro / Global (context)   (Yahoo 全球指数, FRED/UST — 仅上下文, 不翻方向)
                 │
                 ▼
        Policy / Institutional      (当前=LLM 理解层, 非可回测特征)
                 │
                 ▼
        Industry ▶ Theme ▶ Theme Transition ▶ Leader   (当前=NEW, 需数据)
                 │
                 ▼
        Capital Flow / Stock Behavior / Fundamental Catalyst
                 │
                 ▼
 ┌────────── Local Quant Alpha (数学事实, §37) ──────────┐
 │  短窗特征 → walk-forward LGBM → 截面打分 → 期望收益/概率 │
 └───────────────────────┬───────────────────────────────┘
                         ▼
        Candidate Generation  (5000 → 1200 → 200 → 50, 见 §3 漏斗)
                         ▼
        LLM Intelligence (信息理解, §38)  ─── 50 → 20
                         ▼
        Contrarian / Red Team            ─── 20 → 10~15
                         ▼
        Quant ⊕ LLM Fusion  → T+1/T+2/T+3/T+5 预测 + 双可信度
                         ▼
        Opportunity Ranking → RECOMMENDATION_{date}.json  (immutable 冻结, §43)
                         ▼
        Paper Portfolio (资金/手数/相关/T+1) → PAPER_PLAN → Ledger
                         ▼
        Outcome Tracking (T+1/T+3/T+5 实际 vs 预测) → Model Evaluation
```

---

## 2. 逐段：复用锚点 + PIT 门 + 失败行为

| 段 | 输入→输出 | 复用锚点 | PIT 门 | 失败/降级 |
|----|-----------|----------|--------|-----------|
| External→Raw | 增量拉 D1（未来分钟）/东财/Yahoo | `ml1_live/panel.py::update_bars`,`layers.py`,`global_north.py` | 只取 `(frozen_end, asof]` | 单票挂→`BAR_HANG` 跳过；源黑名单→退避 `--skip-fetch` |
| Raw→PIT→Pack | 归一+冻结块逐位复制+live_hash | `panel.py::build_live_pack`,`pit.py` | `asof<frozen_end` 拒写；`knowledge_ok` | 核心缺→`DATA_FAILED`→`NO RECOMMENDATION`（§27） |
| Market State | pack→breadth/涨停/换手 z/trend | `alpha_v2/signals.py`,`regime/state.py`,`v38_overlay/sentiment.py::_roll_z` | 阈值仅研究窗定 | 缺→降级但标 `DEGRADED` |
| Macro/Global | Yahoo/FRED→context | `global_north.py::yahoo_closes`,`macro_v17`（哈希） | 冻结哈希/缓存时点 | 非核心，缺→`UNAVAILABLE` 不置 0（§28） |
| Policy/Theme/Leader | 文本/概念→理解 | **NEW**（LLM 层）+ `information_v16` 行业 | LLM 联网=**非 PIT**，只做门不做特征 | 缺→Quant-only，标 `INFORMATION_CONFIDENCE=DEGRADED` |
| Local Quant Alpha | 特征→截面分/期望收益 | `ml_v25/model.py`,`features.py::ranked_row`,`ml_v33` 骨架 | `EMBARGO=hold+1`,`cutoff=s-EMBARGO`,禁用窗锁 | 模型异常→`MODEL_FAILURE`（§7 分类） |
| Candidate Gen | 分数→候选集 | `opportunity/score_v2.py`,`select.py` 硬闸 | 只用 close(t) 可知信息 | 候选=0→进 Opportunity Suppression Audit（§7） |
| LLM Intelligence | 候选 50→深度 20 | `paper_fusion.py::layer_b_prompt`,`cursor_cloud.py` | `priced_in`/三时钟；web=非回测 | LLM 超时/`UNKNOWN` 多→`LLM_PARTIAL` |
| Red Team | 20→10~15 | `paper_fusion.enforce`（截断）；红队=NEW 代码 | 同上 | 全被否→NO_TRADE 合法（§5） |
| Fusion→Rec | 融合→排名→冻结 | `v8_fusion/states.py` 每态带经济句 | 冻结即 immutable | — |
| Paper | Rec→可执行组合→撮合→账本 | `paper_ops.py::derive_account`,`capital_ref.py`,`_exit_fill` | T+1、涨跌停不成交、成本 | 撮合失败→`PAPER_FAILED`（不改 Rec） |
| Outcome | 结算 T+1/T+3/T+5 | `books.py`,`scale_book::daily_curve` | 实际开盘价才结算（幂等） | 缺价→挂起，不臆造 |

---

## 3. 候选漏斗（§35，LLM 不吃 5000 只全量）

```
5000+ 全市场
   │  Local Quant（规则/流动性/ST/停牌/涨跌停/成本可行性）
   ▼
~1200  可交易 universe
   │  Local Alpha（短窗模型截面打分）
   ▼
~200   高分候选
   │  Candidate Set（机会分闸: mechanism/economic_reason/data/cost_survival/novelty）
   ▼
~50    进 LLM 深度分析（逐只结构化 JSON + 证据 ID）
   │  LLM Deep Analysis（事件/政策/主题/资金 理解）
   ▼
~20    红队/逆否审查（Contrarian）
   │  Red Team（priced_in / narrative vs hard_event / 反面证据）
   ▼
10~15  Final Fusion（Quant⊕LLM，双可信度）
   ▼
Top 3~15  用户先看的推荐（§57）
```
- **LLM 每次只吃「候选子集 + 该子集相关证据」**，禁止「5000 股 + 全新闻 + 全 policy → 一次 API」（§35）。
- 每层过滤都写快照（可回答「为什么 9/15 早上 9 点推荐这只」，§43），可追溯到 Fusion→Model→Features→Theme→Leader→News→Policy→Raw Evidence。

---

## 4. Recommendation ≠ Paper（再次强调，§42）

```
RECOMMENDATION_{date}.json     (Alpha 层, immutable, 不看钱)
   A=S  B=A  C=A  D=B  E=B
            │  Account/Lot/T+1/相关/成本
            ▼
PAPER_PLAN_{date}.json         (Portfolio 层, 看钱)
   实际可能只执行 A, C   (¥20k 买不起全部 → Executable NO/YES 分层, §15)
```
资金规模变 → 只重算 `PAPER_PLAN`，**不重算 alpha**（§16）。

---

## 5. 失败传播总则

- **核心（Price/Calendar/Universe）失败 → 全链停在 `DATA_FAILED`，不出推荐**（§27），不拿旧数据偷偷续。
- **非核心（News/Policy/Macro）失败 → 降级 Quant-only，打标 `DEGRADED`/`UNAVAILABLE`（非 0）**（§28）。
- 每源 STATUS/LAST_SUCCESS/RETRY/COVERAGE/FRESHNESS 上报 GUI Data Health（§26/§29）。
- 连续 10/20/30 日交易极少 → Opportunity Suppression Audit，产出 `TRUE_NO_EDGE / SYSTEM_TOO_STRICT / DATA_FAILURE / MODEL_FAILURE / PIPELINE_FAILURE`（§7）。
