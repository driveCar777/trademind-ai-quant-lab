# A_SHORT_FEATURE_REGISTRY_V2.md

> 特征登记表（V2）。**只登记，不实现。** 每个特征：`feature_id / name / category / formula / frequency / PIT / risk`。
> 唯一**已实现** = `PRICE_MOM_20D`（baseline/CONTROL）。其余全部 REGISTERED（未编码），实现须新预注册合同。
> PIT 列：所有价格/量特征只用 ≤ 收盘(T) 的信息，成交在 open(t+1)。risk 列标注该特征最大的证伪风险。

---

## Layer 0 — Regime
| feature_id | name | category | formula (概念) | freq | PIT | risk |
|---|---|---|---|---|---|---|
| REG_IDX_TREND | 指数趋势 | regime | HS300 close/MAn − 1 | D1 | ✅ | 趋势滞后 |
| REG_IDX_VOL | 指数波动 | regime | HS300 已实现波动(20d) | D1 | ✅ | 波动≠方向 |
| REG_MKT_LIQ | 市场流动性 | regime | 全市场成交额/换手 z | D1 | ✅ | 结构性上移 |
| REG_FX_RMB | 汇率 | regime | USDCNH 变动 | D1 | ✅ | 与个股弱相关 |
| REG_OVERSEAS | 海外 | regime | 隔夜美股/亚洲指数 | D1 | ⚠ 时区对齐 | O4 已 REJECT |

## Layer 1 — Theme / Information（多为 NEW 数据，见 DATA_REQUIREMENT）
| feature_id | name | category | formula | freq | PIT | risk |
|---|---|---|---|---|---|---|
| THEME_MONEYFLOW | 板块资金集中 | theme | 板块主力净流入 z | D1 | 需 captured-time | 数据付费/缺 |
| THEME_NORTH_IND | 北向行业流向 | theme | 行业北向净买 | D1 | ⚠ 2024-08 停发 | 数据停发 |
| THEME_LHB | 龙虎榜热度 | theme | 上榜频次/席位 | 事件 | 公告时点 | 无代码 |
| THEME_NEWS_FREQ | 新闻频率 | theme(info) | 题材新闻计数 | 事件 | published/knowledge_time | 结构不可回测(需语料) |
| THEME_POLICY | 政策催化 | theme(info) | 政策事件→板块映射 | 事件 | 同上 | DATA_BLOCKED |
| THEME_ANNOUNCE | 公告事件 | theme | 预告/增减持/回购 | 事件 | 原始公告日 | 有代码未接 |

## Layer 2 — Stock Selection（价格/量，可 PIT，优先）
| feature_id | name | category | formula | freq | PIT | risk |
|---|---|---|---|---|---|---|
| **PRICE_MOM_20D** | 20日动量（**已实现/CONTROL**） | price | close(t)/close(t−20) − 1 | D1 | ✅ | 小盘 β / 中周期非短线 |
| PRICE_MOM_5D | 5日动量 | price | close(t)/close(t−5) − 1 | D1 | ✅ | 短反转污染 |
| PRICE_REV_3D | 短反转 | price | −(close(t)/close(t−3)−1) | D1 | ✅ | 微观结构噪音 |
| OVERNIGHT_GAP | 隔夜跳空 | price | open(t)/close(t−1) − 1 | D1 | ✅ | 停牌/除权干扰 |
| VOL_BREAKOUT_5D | 量能突破 | volume | vol(t)/mean(vol,5) | D1 | ✅ | 一字板/异常量 |
| TURNOVER_SPIKE | 换手异常 | turnover | turn(t) z-score | D1 | ✅ | 微盘换手偏高 |
| RANGE_POSITION | 区间位置 | price | (close−min)/(max−min, n) | D1 | ✅ | 趋势/震荡混淆 |
| VOLATILITY_20D | 波动率 | price | std(ret,20) | D1 | ✅ | 高波动=高风险 |
| BREAKOUT_NDAY | N日新高突破 | price | close(t) ≥ max(high,n) | D1 | ✅ | 假突破 |
| REL_STRENGTH | 相对强度 | cross | 个股 − 板块/指数收益 | D1 | ✅ | 需板块数据 |
| LIMIT_UP_CONTINUATION | 涨停延续 | event | 昨涨停→今表现（**新合同，非 V33**） | D1 | ✅ | V33 判"不可交易"；须独立证明 |
| RECENT_LIMIT_UP_CNT | 近端涨停计数 | event | 近 n 日涨停次数 | D1 | ✅ | 彩票效应 |
| SECTOR_STRENGTH | 板块强度 | theme→sel | 板块动量排名 | D1 | ✅ | 需行业数据 |
| LEADER_SCORE | 龙头分 | cross | 板块内相对强度+量能+涨停 | D1 | ✅ | 需板块+资金 |

## Layer 3 — Risk（报告叠加/可执行子宇宙，不偷改 baseline）
| feature_id | name | category | formula | freq | PIT | risk |
|---|---|---|---|---|---|---|
| RISK_ST | ST 标记 | risk | isST | D1 | ✅ | baseline 默认含 ST |
| RISK_ADV | 流动性/ADV | risk | mean(amount,n) 门槛 | D1 | ✅ | 加门=改 universe（禁；仅叠加报告） |
| RISK_ABN_VOL | 异常波动 | risk | 波动分位 | D1 | ✅ | 误伤强势股 |
| RISK_FIN | 财务风险 | risk | 亏损/退市风险 | 季 | 原始公告日 | 需财务接入 |
| RISK_VALUATION | 估值过高 | risk | PE/PB 分位 | D1/季 | ⚠ | 短线相关性弱 |

---

## 登记纪律
- **实现任一非 CONTROL 特征 = 新预注册合同**（新窗/OOS/成本/hold/执行假设；计多重性 m）。
- Layer 2 数值因子优先（可 PIT、Cloud 只需 D1 pack）；Layer 1 信息/新闻/政策**最后**（需 timestamped 语料，Phase D）。
- 每个因子须打过 EW-eligible + size-bucket EW + `PRICE_MOM_20D` 三基准 + 净后成本 + OOS + FDR 才算 selection alpha。
- `LIMIT_UP_*` 系列**不得复用/修改 V33**；须全新独立合同并独立证明（Decision A-003）。
