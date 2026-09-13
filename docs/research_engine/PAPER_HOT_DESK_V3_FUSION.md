# Paper Hot Desk V3 — 融合台（ML1 + Grok 两层）

**日期：** 2026-09-11  
**端口：** `http://127.0.0.1:9001/paper`（默认视图「融合」；三本对照账在「对照账」开关下，未删）  
**主线冻结：** `:9000/paper`（V2.1 / V26.8）、`daily.py`、`paper_ops.py`、ML1 特征/分数/外壳 **一字不改**。  
**定性：** 纸面实验。**不是 Candidate、不是 Level-1、不是收益承诺。** 联网层无法回测。

## 0. 一句话

一条管线：ML1 名单为池 → Layer A 让 Grok **只看匿名 K 线**过滤 → Layer B 让 Grok **联网**给仓位与买卖 → 本地**硬规则截断** → 出计划 JSON，用户手工登记成交。两次 Grok，按 Cursor 额度计费。

## 1. 用户要什么 / 系统给什么

| 用户要 | 系统给 | 系统不给 |
|---|---|---|
| 把三本融合成一台 | 一条管线、一个默认页面；三本降级为「对照账」审计账本 | 不删三本，不混算三本 |
| 用强云模型联网（资金流/地缘/板块） | Layer B 允许联网，reason 必须写来源类型与时效 | 不允许联网层挑池外票 |
| 加上本地 ML1 | 池只来自 ML1 `SHORTLIST_*.json` + `SIGNAL_*.json` 前 30 | 不发明新本地模型；不改 ML1 |
| 更激进、更高收益 | 换手更高（每日可出计划）、仓位由 Layer B 给 | **不承诺收益**。激进 = 费用先走 |

## 2. 管线（每个交易日晚上，`:9000` 数据更新之后）

```
a. 池   = 最新 SHORTLIST_{date}.json（V26.8 口径，≈10 只）
         ∪ SIGNAL_{date}.json 按 score 前 30（主板 sh.60/sz.00，收盘 ≤ ¥100）
b. Layer A（匿名，账本2 同协议）
         60 根 OHLC：冻结包尾部（≤2026-08-28，只读）+ live/bars 增量，截至 asof
         首收盘归一 100，id=U01…，无代码/名称/日期/成交量
         anon.assert_clean() 断言无泄露 → Grok（禁网、禁猜代码）→ keep[]
         写 live/paper_hot/FUSION_ANON_LOG.json（sent/keep/map/status，最近 60 条）
c. Layer B（联网）
         输入：keep 的名字 + 代码 + ML1 rank/score + 收盘、当前持仓（含 sellable_at_fill）、现金/权益、硬规则
         输出 JSON：exposure_pct(0–100)、regime、themes[{tag,note,source}]、
                   names[{symbol,action∈BUY|HOLD|SELL,lots_hint,reason,tag,source}]、avoid[]、confidence
d. 硬规则截断（enforce()，确定性，冒烟 25 覆盖）
         成交 = 下一交易日开盘（fill_date）
         T+1：buy_date ≥ fill_date 的持仓不能 SELL → 改 HOLD 并标 blocked
         BUY 只能是 keep 内 + 主板 + ≤¥100；SELL 只能是持仓；池外/非主板/未持有 → dropped[] 带 why
         BUY/HOLD 合计 ≤ 8 只（多出的 BUY 截掉）
         总名义（保留持仓市值 + 新买）≤ exposure_pct × 权益；新买 ≤ 现金 − ¥200
         手数：Grok lots_hint，缺省 floor(2000 / (100×收盘))；按预算逐手减到合规
         Layer A 失败 → keep 为空 → 没有 BUY；Layer B 失败 → exposure 记 0 → 没有 BUY
         Grok 未提及的持仓 → 默认 HOLD（没有任何东西会自动卖）
e. 产物  live/paper_hot/FUSION_PLAN_{asof}.json、FUSION_LAST.json、FUSION_RUN.json
         成交日志仍是 live/paper_hot/JOURNAL.json（与账本3 同一本；用户手工登记；不自动执行）
         逐日盯市 = paper_ops.derive_account（只读导入）按 live/bars 最后收盘
```

## 3. 接口（只 `:9001`）

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/v1/hot/fusion` | 最近计划 + 运行状态 + 融合台账 + 账本2 门 |
| `POST` | `/api/v1/hot/fusion/run` `{model?}` | 后台线程跑管线（两次 Grok）；同一时间只跑一个 |
| `POST` | `/api/v1/hot/fusion/stop` | 取消当前 Cloud Agent run |

`FUSION_RUN.json` 与 `BRIEF_RUN.json` 同一套 Windows 安全写入 + 死线程校正（`running=true` 且线程不在 → 标失败）。

## 4. 页面（`paper_hot.html`）

- 顶栏开关：**融合**（默认）/ **对照账**（账本1/2/3 原样）。
- 融合视图最前面四个数：**建议仓位（硬规则后）**、**权益/现金**、**本计划估费（= 权益 %）**、**账本2 是否读完**。
- 计划表：动作 / 手 / 参考价 / 估金额+费 / 理由与来源 / 登记按钮（T+1 锁的显示原因）。
- 「两层怎么走的」：池构成、Layer A n_in→n_keep + 无泄露、Layer B 原始仓位/自评信心/用时、回避。
- 「被硬规则截掉的」：Grok 说了但不合规则的每一条 + why。
- 账本2 未满 29 期时固定显示 **「账本2 未读完，匿名过滤增量未知」**。
- 色板：`#070b12` / `#111827` / 蓝 `#3b82f6` / AI 紫 `#7c5cfc`；无酒红。

## 5. 诚实条款（写进页面与 JSON）

1. **Layer B 无法回测**：网上的信息带前视，在历史窗上评它就是作弊。只能前向记纸面日志。
2. **「激进」= 换手更高、费用更高**，不是边更大。¥20k 每笔最低佣金 ¥5，费用先走；页面把估费放在前三个数里。
3. **不是 Candidate**：融合台任何数字都不进研究合同、不改 ML1 / V26.8、不改 `:9000`。
4. Layer A 是否有增量，只由账本2（29 期验证窗）回答；读完前一律「未知」。
5. 系统不发单。

## 6. 账本2 超时修复（同日）

- `grok_keep.ask_keep`：每期 2 次尝试、单次 420 s；超时先 `cancel_run` 再归档；全部失败抛 `GrokTimeout`。
- `book2.run_window`：捕获 → 该期记 `status=GROK_TIMEOUT, keep=None, ret=0`，**不计入 TWR**、`n_timeout` 单独计数、不计当月定投；run 标 `stopped_reason=GROK_TIMEOUT` 并停止。再点「跑验证窗」从该期续跑（尾部 GROK_TIMEOUT 期被弹出重试；前缀不变，不会重来）。
- 绝不把超时当 keep-all / keep-none。
- **诊断（当晚）**：真正原因是传输——`api.cursor.com` 约一半请求在 TLS 层断（`SSL UNEXPECTED_EOF` / `record layer failure`、偶发 502），`create_agent` 没发出去。修：`cursor_cloud._request` 传输重试 5×（8 s）、`wait_run` 容忍轮询失败、默认 900 s；`grok_keep` 每期 1 次重试 × 900 s。
- **匿名协议 v1.1**：`bars=[[o,h,l,c],…]`（时间顺序、2 位小数、索引隐含），payload 多 `protocol`/`cols` 字段；信息与 v1.0 相同，体积约一半（10×60 ≈ 12 KB）。泄露断言不变。`B2_LEDGER.json` 记 `anon_protocol`；09-10 的单期一枪是 v1.0。

## 6b. N5 集中读数（对照账第四本）

合同 `HOT_N5_CONCENTRATION_CONTRACT.md` 跑前写；`book_n5.py` = 账本1 引擎、只改 `n_target=5`、只读 VALIDATION 一次 → **`HOT_N5_CONCENTRATION_NOT_VIABLE`**（TWR −0.79% vs +39.03%；逐日 MaxDD −28.1%；打过账本1 8/29 期；超额均值 −1.19%/期 t −2.03）。集中不是可用的"激进杠杆"。不试别的 N。

## 7. Grok 设计评审：采纳 / 拒绝

原文见 `PAPER_HOT_DESK_V3_GROK_CONSULT.md`。规则：只采纳关于**日志 / 提示词结构 / 风险展示**的建议；任何触及 ML1 / V26.8 / 池来源 / 回测的建议一律拒绝。

评审 2026-09-11 23:02 回（grok-4.6 xhigh fast，107 s）。总评一句话：「这不是给冻结 ML1 加壳，而是一台日频裁量机，只用 ML1 当候选生成器」——我们接受这个描述，页面上也这么写。

### 采纳（已落代码）

- `priced_in` 硬规则：Layer B 每条非 HOLD 自报 `claim_class`（hard_event / narrative）与 `priced_in`；`priced_in=true` 的 BUY 丢弃、SELL 降 HOLD。这是把「下一开盘成交」假设写死，不是择时。
- 提示词默认 HOLD、允许空 `names` 只给 `avoid`。
- 计划 JSON `audit` 块：`hold_all`、`n_narrative_actions`、`n_unspecified_actions`、`truncation_rate`、`invested_pct_after_plan` vs `exposure_pct_asked`；`prompt_hash`（改提示词 = 新序列）；`anon_protocol`。
- 首屏只放能打脸的数（exposure / 现金 / T+1 锁定 / 估费 / 截断）——已如此，不改。

### 拒绝（记为已知风险）

- 池收窄到当日 V26.8 十只；`exposure_pct` 收回；Layer B 不产 SELL；改 20 日频；账本2 揭盲前 Layer A 不进决策——均与用户"更激进、日频、联网叠加"的明示要求冲突，保留原设计，用 `audit` 块与「计划 vs 登记」偏离在几个月后看。
- 平行「只执行 Layer A keep」第四本：有价值，本轮不加；`FUSION_ANON_LOG` 已记每晚 keep，可离线复算。

### 已知失败模式（Grok 列，全部认同，写在这里不写代码）

追已公开新闻买在开盘；T+1 锁死次日反转；¥5 地板磨损；30 尾部主题替换短名单；手工登记挑好成交；A/B 同屏互相合理化；揭盲前偷看账本2 改 prompt；`exposure_pct` 变成恐惧/贪婪旋钮；把纸面净值当能力证明。

## 7b. 自动纸面登记（2026-09-12，用户：「让他每天的建议，都纸面登记模拟买卖」）

`paper_fusion_fill.py`。每个计划到了 `fill_date`、`live/bars` 有该日开盘价，就把 BUY/SELL 按**开盘价 + 估算费用**自动写进热台 `JOURNAL.json`（事件带 `auto=true`、`plan_id`、`note="FUSION auto {asof}"`）。规则与手工登记完全一样：先卖后买、T+1 当日买入不可卖、买入不超过现金 − ¥200（手数向下取整）、未持有不卖。审计 `FUSION_FILLS.json`（请求 vs 成交 vs 跳过原因）；幂等，重跑不重复。开关「自动纸面登记」默认开，关掉只是不登记。

每日驱动 `POST /api/v1/hot/fusion/daily` = 结算 → 行情新鲜才跑融合管线（否则 `SKIPPED_STALE_DATA`，不调 Grok；已有当日计划 `SKIPPED_ALREADY_PLANNED`）。任务计划 `TradeMind_HotFusionDaily` 19:30 周一至周五调 `scripts/hot_fusion_daily.bat`；**它不碰 :9000 的更新按钮**，用户先更新行情它才有新鲜数据。

诚实声明：自动成交是**模拟**（下一开盘价、估算费用），没有任何真实下单；账本上的数字是纸面，不是 Candidate、不是承诺。Grok 评审第 iv-7 条「计划 vs 登记偏离」在自动登记下变成「计划 vs 模拟成交」——偏离只剩 T+1 / 现金地板 / 无 K 线三种，全在 `FUSION_FILLS.skipped` 里。

## 7c. 实时诊股叠加合同（2026-09-12 10:51，用户决定；2 个月观察）

**决定。** `:9000` 的 ML1 + V26.8 仍是唯一**名字来源**；`:9001` 在它上面叠一层稀疏的 Grok 4.6 实时诊断（BUY / SELL / ADD / REDUCE / REPLACE / HOLD），只纸面登记；用户在同花顺手工跟单，看约 2 个月。**Layer A（匿名过滤）在实时场次不再使用**：账本2 29/29 TWR +3.3% vs 账本1 +39.0% 已在案，匿名过滤减分——结果保留，不再复算、不再作为缩池闸门。

**场次（Asia/Shanghai，周一至五，不常驻，不轮询）。** 09:35 / 11:30 / 15:05 在**能卖或能买**时各最多 1 次 Grok（`SKIPPED_ALREADY_PLANNED` 同场次不重复）；不能买卖则白天 `SKIPPED_NO_CAPACITY`。19:30：当天还没诊过 **必须看一次**（T-1 也看），写成 close 计划；白天已诊过且行情陈旧才 `SKIPPED_STALE_DATA`。**永不第 4 次计费调用**（`MAX_GROK_CALLS_PER_DAY=3`）。不是问句：计划按下一开盘自动记台账。主人只在工作日晚上更新 :9000，所以盘中/收盘允许 T-1 日线 + 联网。非交易日 `SKIPPED_NOT_TRADING_DAY`。详见 SPEC §29.11e。

**时钟分裂。** `clocks.local_asof` = 盯市/名单（通常 T-1）；Grok 网上 = 今天；`fill_date` = 下一开盘。三套不一致是设计。`last_close` 不是今收。日历被截断时 `resolve_fill_date` 按工作日往后走。

**宇宙夹紧（:9001 自有池，不写 :9000）。** 允许动作的股票 = `live/paper_hot/POOL.json` ∪ 当前持仓。池外 → `OUT_OF_UNIVERSE`。合适就买当前热台池；不合适刷新热台池（只读 ML1 SIGNAL 当井，本场不二次问 Grok）。周一 `asof>=2026-09-14` 才启用；此前持仓不动。计划钉 `cash_policy` / `name_source` / `pool_age` / `pool_refresh`。默认 HOLD；`priced_in=true` 的 BUY 丢弃、SELL 降 HOLD（不变）。详见 SPEC §29.11f。

**ADD / REDUCE / REPLACE 的约束（`paper_fusion._expand_actions` + `enforce`）。**
- ADD = 对**已持有**名字再买 `lots_hint` 手（1 手 = 100 股，按盯市价估）；未持有 → `ADD_NOT_HELD`。不受 ≤8 只计数（同一只）。
- REDUCE = 对已持有名字部分卖出 `lots_hint` 手（缺省一半）；≥持仓手数即变 SELL；T+1 未解锁 → HOLD+blocked。
- REPLACE = SELL 持仓 `symbol` + BUY 池内 `replace_with`（`REPLACE_OUT` / `REPLACE_IN` 两行）；新买仍受主板、≤¥100、池内、名义上限约束。
- 全部 BUY 类：名义 ≤ `exposure_pct × equity − 保留部分市值`；金额 ≤ 现金 + 计划 SELL 净额 − ¥200（结算引擎先卖后买，所以卖出净额可用）；手数向下取整，0 手即丢。

**成交。** 每个场次的计划 `fill_date` = 下一交易日开盘；盘中场次不在当天成交、不编造价格，计划先挂 PENDING，由现有结算引擎在 `live/bars` 出现该日 K 线时按开盘价登记。同一 `fill_date` 的多份未结算计划，**后出的覆盖先出的**（先出的标 `SUPERSEDED`，写入 `FUSION_FILLS`）。Grok 在后续场次的 snapshot 里看得到 `pending_plans`，可以确认或改写。

**读取纪律。** 观察从 2026-09-12 起；**只读一次**，时间 = 满 24 个已结算融合期或 2026-11-12，取**更晚**者。中途不为追收益改提示词、阈值、场次、仓位公式（任何改动 = 新合同、计 m）。叠加层**不是 Candidate**、不是 Level-1、不是承诺；账本2 结论留案；Grok 不能扩池；ML1 / V26.8 / `:9000` 不动；无真实下单。

## 7d. MT5 执行 vs 持有（研究结论仍有效；2026-09-12）

见 `docs/research_engine/MT5_EXECUTION_VS_HOLDING.md`。D1 CFD 家族已撞成本天花板；更频繁 = 更频繁付成本。**不是 Candidate。**

## 7e. 热台 MT5 分品种 demo（2026-09-12 11:11，用户要求 :9001 也搞 MT5 / Ava demo）

执行台，不是新边。设计见 `docs/research_engine/PAPER_HOT_MT5_DESK.md`。报价走终端，和 A 股晚上更新不冲突。黄金/原油/欧美/美日/美英/美加/美瑞分账；股票篮子只建议。每天 2 次 Grok（08:30 / 20:30），0.01 手，demo 才发单，实盘拒绝。不重开 V1–V8 / V30 / V32，不训新模型。

## 8. 产物路径

`data/market/cn_a_share/live/paper_hot/`：`FUSION_PLAN_{asof}.json`（晚间两层）、`FUSION_PLAN_{date}_{open|lunch|close}.json`（实时场次）、`FUSION_LAST.json`、`FUSION_RUN.json`、`FUSION_ANON_LOG.json`、`FUSION_FILLS.json`、`FUSION_SETTINGS.json`、`FUSION_DAILY_RUN.json`、`FUSION_SESSIONS.json`（每日场次记录 / 调用次数）、`FUSION_DAILY_CRON.log`、`JOURNAL.json`（共用）。从不写 `live/paper/JOURNAL.json`、冻结目录、`live/signals/`。

## 9. 冒烟

`tests/smoke/25_hot_fusion.py`（`TRADEMIND_HOT_SMOKE=1` → 两层 Grok 都走本地 stub，$0）：文件隔离、池只来自 ML1、匿名 payload（冻结尾 + live bars）无泄露、T+1、≤8 只、名义上限、现金留 ¥200、Layer 失败 → 无 BUY、`FUSION_RUN` 死线程校正、账本2 GROK_TIMEOUT 记录 + 续跑重试、场次枚举与同日去重、实时场次不调 Layer A、发明代码 `OUT_OF_UNIVERSE`、ADD/REDUCE/REPLACE 手数与预算、`scripts/hot_fusion_session.bat` 存在。
