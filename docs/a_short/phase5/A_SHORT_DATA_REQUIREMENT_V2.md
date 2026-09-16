# A_SHORT_DATA_REQUIREMENT_V2.md

> 所需数据集定义。每项：source / frequency / history / PIT / storage + 现状。**不采购、不换源、不改 hash（当前禁）；此为需求清单，不是采集指令。**
> 现状口径针对 Cloud checkout（bulk 多为 gitignored/manifest-only）。

---

## 最小地板（Phase 5 实现前必须具备）
> 没有这四样，一切 empirical 免谈（Phase 4 STOP）。
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| **D1 OHLCV pack** | 冻结 `tm-ashare-EQUITY-D1-...`（BaoStock 冻结） | D1 | 1990–2026-08 | 上市/退市/preclose PIT | raw csv → npy pack | **BLOCKED（字节不在 Cloud）** |
| 交易日历 | BaoStock 冻结 | D1 | 1990– | — | csv | ✅ present |
| PIT universe | 派生 basics | D1 as-of | — | listing/delisting known-date | json/csv | ✅ present |
| 指数日线 HS300/500/1000 | Eastmoney/BaoStock | D1 | 多年 | — | csv | 🟡 HS300/ZZ500 present；1000 待补 |

## Price
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| 日线 OHLCV | 冻结 pack | D1 | 全历史 | 是 | npy pack | BLOCKED（Cloud） |
| 分钟 bars | BaoStock/其它（免费深度未测） | 1min/5min | 需攒 | 是 | 新 pack（NEW） | 🔴 无代码（Track B，稍后） |

## Market
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| 指数日线 | Eastmoney/BaoStock | D1 | 多年 | — | csv | 🟡 部分 present |
| 指数成分 | BaoStock 月度 | M | 月度网格 | as-of | csv | 🟡 manifest-only |
| ETF | BaoStock | D1 | — | — | csv | 🔴 未做（A-Short 用） |
| 行业分类 | BaoStock 月度 | M | — | as-of | csv | 🟡 有代码未接 |

## Capital
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| 北向（市场级） | Eastmoney | D1 | –2024-08 | captured-time | json.gz | 🟡 缓存 present；⛔ 个股北向停发 |
| 个股资金流（主力净流入） | Eastmoney/TuShare | D1 | — | captured | 新表（NEW） | 🔴 无代码，多付费 |
| 换手/成交额 | pack 字段（amount/turn） | D1 | 随 pack | 是 | pack | ✅（随 D1 pack） |
| 龙虎榜 | 交易所（免费需采集） | 事件/D1 | — | 公告时点 | 新表（NEW） | 🔴 零代码 |

## Company
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| 财报 4 表 | Eastmoney/BaoStock | 季 | 多年 | **原始公告日** PIT | npy/json | 🟡 有代码未接、manifest-only |
| 业绩预告/快报 | Eastmoney | 事件 | 多年 | 公告时点 | npy/json | 🟡 有代码未接 |
| 公告（一般文本） | 巨潮/交易所 | 事件 | — | 公告时点 + content_hash | 语料（NEW） | 🔴 仅 `.gitkeep` |
| 行业 | BaoStock | M | — | as-of | csv | 🟡 有代码未接 |
| 市值/股本 | BaoStock/Eastmoney | D1/事件 | — | 是 | 表（NEW） | 🔴 无独立适配器 |

## Alternative
| 数据 | source | freq | history | PIT | storage | 现状 |
|------|--------|------|---------|-----|---------|------|
| 财经新闻 | 需采集/供应商 | 事件 | 需攒 | published/captured/knowledge_time/content_hash | timestamped 语料（NEW） | 🔴 ⛔ 无代码、付费/合规 |
| 政策（国务院/发改委/央行/行业） | 官网/供应商 | 事件 | 需攒 | 同上 | timestamped 语料（NEW） | 🔴 ⛔ |
| 宏观/汇率/海外/商品 | immutable 冻结 | D1 | present | — | csv | 🟡 present 未接 |

---

## PIT 硬要求（所有新数据）
- 结构化事件：存**原始公告/披露时点**（非修订时点），同期取最早版本。
- 文本（新闻/政策）：存 `published_time / captured_time / knowledge_time / source / content_hash`；**无 timestamped 语料前不得做历史回测**，只进实时 shadow。
- 任何新数据集：新 `dataset_id` + hash + 新预注册合同；**不改冻结 lineage、不采购、不换源（当前禁）**。

## 存储格式约定
- 参考层：csv（日历/basics/universe）。
- 面板/特征：npy pack（T×N）+ meta（dataset_id/hash）。
- 事件层：normalized npy + PIT.json（沿用 v23/v24/v38 约定）。
- 大件一律 gitignore（`DATA_STORAGE_POLICY.md`）。

## 结论
**当前唯一阻塞 = 最小地板里的 D1 pack 字节。** 其余数据分层按 ROADMAP 逐步补，多数"有代码未接"（复用现成适配器），少数（龙虎榜/资金流/新闻政策/分钟/市值）"无代码需新建"，且部分受付费/合规/停发限制。
