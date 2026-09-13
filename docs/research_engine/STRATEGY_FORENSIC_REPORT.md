# STRATEGY_FORENSIC_REPORT

> 2026-09-13。只读取证。不改核心代码、不重训、不调参。  
> 从代码反推真实交易逻辑，不采信 README / 页面文案。  
> `candidate=false`。不是新策略。

## 0. 第一结论：这里没有「一套」MT5 自动交易系统

仓库是研究实验室 + 几条互不相通的执行口。把它们当成同一个会稳定赚钱的机器人，是对架构的误读。

| 层 | 代码 | 信号从哪来 | 会不会 `order_send` | 和回测是不是同一套逻辑 |
|----|------|------------|---------------------|------------------------|
| A. 热台 demo 观察台 | `master/api/app/service/paper_hot_mt5.py` | **Grok 大模型**读实时快照 | demo 且 `demo_send` 且 `TRADEMIND_MT5_SEND≠0` 才会 | **否。回测模型不进提示词** |
| B. V9 人手确认单 | `order_service.py` | 研究摘要里 **正则抠 RSI**，≥70 空 / ≤30 多 | 人手 `confirm=true` + demo | **否。与 V4/H1 无关** |
| C. 研究坟场 D1 V1–V5 / H1 V1–V9 / V30 / V32 | `research_engine/hot_mt5_*` | 树 / 规则 / 截面 | **永不发单** | 自己跟自己比 |
| D. 黄金 V4 跟盘展示 | `hot_mt5_gold_follow/stance.py` | `sign(close/close_252−1)` | **否**（`order_send=false`，且**不写入 Grok**） | 只展示冻结日线状态 |
| E. A 股 :9000 / ML1 | `daily.py` / `paper_ops.py` | LightGBM 截面 | 禁止 MT5 | 另一市场 |

截至本审计：`live/paper_hot/MT5_SETTINGS.json` 为 `demo_send=true`、`volume=0.1`（默认 0.01 的十倍）。`MT5_JOURNAL.json` / `MT5_LAST.json` / `MT5_SESSIONS.json` **不存在**。本机没有热台自动成交账本可对终端权益。层 A 若从未跑过 `run_session`，终端里的亏钱不是这套研究账本，就是人手/Grok/别的 EA。

---

## 1. Entry Logic

必须按层分开。不存在统一的 BUY/SELL 阈值。

### 1.1 层 A — 实际能自动发单的逻辑（Grok）

源：`paper_hot_mt5._prompt` / `enforce` / `execute` / `mt5_service.order_send_demo`。

**BUY（代码语义，不是模型阈值）**

- Grok 对该产品输出 `action=BUY`，且 `priced_in` 不为 true。
- 终端该逻辑品种当前不是多（已多 → `ALREADY_LONG` 丢掉）。
- 有 bid/ask/broker；品种在白名单；不是 `SHARES`。
- 若当前是空：先平空，**不再开多**（提示词写明「平空后不再开」）。
- 然后 `order_send`：`TRADE_ACTION_DEAL`，市价，买用 ask。无价格过滤。

**SELL**

- 对称。已空则丢掉。平多后不再开空。卖用 bid。

**不交易 / HOLD**

- 默认 HOLD。
- `priced_in=true` 的开仓丢掉。
- 未知品种、重复、无报价、周末、当天该场次已跑过、当天已 2 次 Grok、终端离线、实盘账户。
- `SHARES` 永远 `send=false`（V30 成本天花板）。
- `TRADEMIND_HOT_SMOKE=1` 或 `TRADEMIND_MT5_SEND=0` 或设置关掉 `demo_send`：只记账或不跑。

**信号是模型还是规则？**

- **既不是回测里的树，也不是 V4。** 是 Cursor Cloud 上的 Grok，提示词允许「联网看宏观/地缘/央行」，并塞进 snapshot：bid/ask、最近 20 根 **M15 close**、持仓、一句品种 lore（如「黄金是趋势品种」）。
- `gold_follow()` 注释写死：**Never appended to Grok prompts**。

**模型输出 / threshold**

- 输出是 JSON：`BUY|SELL|FLAT|HOLD` + `confidence` 0–100。
- **代码不读 confidence。** 没有 0.5、没有 z-score、没有动态门槛。
- `priced_in` 是模型自报的布尔，系统只用来丢单，没有定义什么叫 already priced。

### 1.2 层 B — V9 RSI 人手单

`order_service.proposal_from_research`：只接受 `preset=indicator`。从 `summary` 用正则抓第一个 RSI。

- RSI ≥ 70 → SELL（超买）
- RSI ≤ 30 → BUY（超卖）
- 中间 / 抠不到 → HOLD
- 人手可覆盖 `side`（`wire_test`）

这是均值回归启发式，**从未当 Candidate**，与黄金研究无关。

### 1.3 层 C — 研究账本（不发单）

共性：信号在 **t 的收盘特征**上产生，**下一根开盘**进，持有 **N 根**后下一开盘出。标签 `y[t] = open[t+1+N]/open[t+1] − 1`。

| 合同 | BUY | SELL | 不交易 | 输出 | 门槛 |
|------|-----|------|--------|------|------|
| D1 V1 / H1 V1,V5,V6,V9 | `score>0` | `score≤0`（**零也做空**） | 分数 NaN | LightGBM/Ridge **回归** | **无。永远在场** |
| D1 V2 | argmax=LONG | argmax=SHORT | argmax=CASH | 三分类 | 标签门槛 = `2×META` 预期成本；实测 10–33bp ≪ 波动，CASH 几乎不出现 |
| D1 V3 | 同上 | 同上 | CASH | 三分类 | `k×ATR√hold`；CASH 标签 79–88%，覆盖失败 |
| D1 V4 / V5 | `close/close_252−1 > 0` | `<0` | `==0`（几乎没有） | **无树** | 无。V5 只缩手数 |
| H1 V2 ORB | 伦敦 07:00 箱体收盘突破 | 对侧 | 无 07:00 或当日出不了 | 规则 | 无过滤；99% 日触发 |
| H1 V3 | 打穿昨日高 / ORB±0.5 ATR | 对侧 | 极少 | 规则 | |
| H1 V4 | 亚洲箱被打穿则 **反手** | 反手 | | 规则 | 92% 日触发 |
| H1 V7 | `sign(score)` 且 `\|score\|>1×ATR` | 对侧 | 门槛下空仓；每日最多 1 笔 | 回归 | λ=1 写死 |
| H1 V8 | 三分类谁先碰 ±1 ATR | | CASH 2.4% | 三分类 | k=1 写死 |
| V30 美股 CFD | LS20 截面 | 空头腿 | | LightGBM | 分位写死；成本门杀死 |
| V32 宏观池化 | LS | | | LightGBM | 已否 |

**threshold 如何确定：** 研究层事前写死（`sign`、λ=2、k、252/20）。**没有**验证集选阈值的代码。  
**是否动态调整：** 不调阈值。Walk-forward 只 **重拟合树权重**（`REFIT_EVERY` 250 根 D1 / 1000 根 H1）。

### 1.4 层 D — V4 跟盘（展示）

`stance.py`：最后一根 D1 `sign(close/close_252−1)` → LONG/SHORT。当前（2026-09-11）LONG，未平腿 2026-08-25 开盘 4679.82。人要跟，得自己点。系统不发单。

---

## 2. Exit Logic

| 机制 | 层 A Grok demo | 层 B V9 | 层 C 研究 | 层 D 跟盘 |
|------|----------------|---------|-----------|-----------|
| TP | **无** | 无 | 无（H1 V3/V8 是障碍触达，不是利润目标） | 无 |
| SL | **无**。`order_send` 请求无 `sl`/`tp` | 无 | 无（路径诊断 BE/TRAIL 是只读，禁止写回） | 无 |
| Trailing | 无 | 无 | 无 | 无 |
| Time stop | 无。仓位可跨很多场次，直到 Grok 说 FLAT/反手 | 无 | **主出场**：D1 hold 5/10/20；H1 hold 24 或当日 ≥20:00 | **20 根 D1** |
| Signal reversal | Grok 下一场 SELL/BUY 当 CLOSE | 下一笔人手 | 非重叠：上一段 `t_out` 才再看信号 | 20 根走完再看 252 日符号 |
| Forced close | 无（除 live 拒绝发新单） | 无 | 样本末不够 hold 则不开 | 无 |
| Session close | 无。08:30/20:30 只是 **问 Grok 的钟**，不是平仓钟 | 无 | H1 V2/V4/V7：当日 ≥20:00 UTC 开盘出 | 无 |

层 A 的市价单：`deviation=30` 点，尝试 IOC/FOK/RETURN。**没有保本、没有移动、没有会话强平。**  
平仓手数用计划里的固定 `volume`，**不是** `position.volume`。账户里若不是正好 0.1/0.01，可能只平一部分。  
`paper_hot_mt5.MAGIC=260912` 未写入请求；真正发出去的 magic 是 `mt5_service.MAGIC=240824`（与 V9 人手单同一标记）。  
黄金 V4 路径诊断（`HOT_MT5_GOLD_V4_PATH_EXITS.md`）：保本 3% 会把全样本 +52% 砍到 +14%；大亏单多数从未有过 +3% 收盘浮盈。

---

## 3. Position Sizing

| 项 | 事实 |
|----|------|
| 手数 | 层 A：设置 0.01–0.10，**当前文件是 0.1**。层 B/研究文案：0.01。V5：`w=min(1, 0.10/σ20d_ann)` 只作跟盘展示上限 |
| 风险百分比 | **无**。不按账户权益算 |
| Leverage | 不在代码里设杠杆；CFD 用经纪商保证金。研究 **禁止为收益加杠杆** |
| 最大持仓 | 层 A：每逻辑品种至多 1 笔（已多不再买）。最多 7 个可发送品种同时在场 |
| 同时交易数 | 每场每品种最多 1 个非 HOLD |
| Pyramiding | **否**（`ALREADY_LONG/SHORT`） |
| Averaging | **否** |
| Martingale | **否** |
| 加仓 | **否** |

研究账本是 **满仓 ±1 或 0**（V5 分数仓），不是金额仓。回测 TWR 是收益连乘，不是 Ava 账户货币。

---

## 4. Regime Assumption（看数学，不看目录名）

| 层 | 代码自称 | 实际数学 | 数据有没有证明 |
|----|----------|----------|----------------|
| A Grok | 「趋势品种，不剥头皮」 | LLM 自由叙事 + 20 根 M15 | **未证明。** 无预注册、无 OOS 账本 |
| B RSI | 指标 | 超买超卖 → **均值回归** | 未当研究合同跑过 |
| D1 V1 树 | TREND_LS | 回归未来 hold 收益 + `sign` **永远多或空** | 7/7 NO。黄金全样本 **−18%**。IC≈0 |
| D1 V4 | TSMOM12 | 12 月动量符号 → **趋势跟随** | 黄金验证 +84% t 2.18，**研究 −10%**，空头 −27%。买持有黄金同期约 +250%。过的是牛市切片，不是独立边 |
| D1 V5 | 波动目标 | 同 V4 + 反比波动缩仓 | 仍是同一边，MaxDD −47→−40 |
| H1 树 | 小时波段 | 猜 **未来 24 根开盘方向**，永远在场 | 真样本内 IC 0.52，44 折 OOS IC **0.038**。过拟合。净 −35%～−67% |
| H1 场次/突破 | ORB / Donchian / 昨日高低 | **突破** | ORB 几乎每天都做；净深负 |
| H1 亚洲反向 | fade | **均值回归** | 年年负，净 −80% |
| V30 | 美股截面 ML | 价格截面 LS20 | 成本天花板。LS −71.5% |
| V32 | 宏观池化 | 多品种一个池 | LS −60.5%，0/5 滚动 |

**没有** regime classifier、没有 RL、没有已部署的 ensemble。  
V2 想做「波动不够就空仓」，门槛矮于波动，**空仓假设被证伪**。

隐含且已被打脸的假设：

1. 价内技术特征能预测未来 5–24 根符号。  
2. `sign(score)` 永远在场的成本可以被边盖住。  
3. 把日线列名搬到小时线仍是「200 日趋势」（H1 `SMA200` = **200 小时 ≈ 8.3 天**）。  
4. 2024–26 金牛上过门的规则，等于可交易边。  
5. Grok 看宏观等于有边。

---

## 5. 配置 / 种子 / 时间 / 品种（扫描项摘要）

- 环境前缀：`TRADEMIND_MT5_SEND`（默认 **"1"**，即允许发单）、`TRADEMIND_HOT_SMOKE`。  
- LightGBM `random_state=25`，无超参搜索循环。  
- 树 **不拟合 scaler**。H1 V6 Ridge 在每折训练集上 z-score。  
- 行情时间戳：`datetime.fromtimestamp(..., tz=timezone.utc)` → `timestamp_utc`。层 A 会话钟是 **本机本地时间** 08:30/20:30（注释写中国时间）。  
- 经纪商黄金符号是 **`GOLD`**，逻辑名 `XAUUSD`。`ALLOWED` 映射在 `mt5_service.py`。  
- D1 拉取会把冻结宏观包 **按时间戳去重合并** 到 live CSV（`pull._merge_rows`）。H1 不预置冻结包。  
- 研究模型 **不落盘 checkpoint** 给推理用；每次研究 run 现拟合。A 股 `REFIT_240` 缓存与 MT5 无关。  
- Mock：`TRADEMIND_HOT_SMOKE=1` 时 snapshot/Grok 全 stub，不连终端。

---

## 6. 真实策略一句话

> **能自动下单的那条路，是「一天问两次大模型，按它的 BUY/SELL 市价 0.01–0.1 手，没有止损」。**  
> **量过的那条路，是「价内树永远在场」或「12 月动量抱黄金牛」，前者证伪，后者不是 Candidate，且不接线到发单。**

把这两句话焊在一起当「系统策略」，就是亏损叙事对不上账本的根因。
