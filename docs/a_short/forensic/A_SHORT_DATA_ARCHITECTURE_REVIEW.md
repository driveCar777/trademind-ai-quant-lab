# A_SHORT_DATA_ARCHITECTURE_REVIEW.md

> 每日 09:00 短线推荐所需数据：**需要什么 / 仓库已有（代码 & 字节）/ 缺什么**。字节列针对**当前 Cloud checkout**（bulk 数据 gitignored，多为 manifest-only）。

---

## 1. 行情
| 数据 | 需要 | 代码适配器 | Cloud 字节 | 结论 |
|------|------|-----------|-----------|------|
| 日线 D1 | ✅ 核心 | `cn_a_share/acquire+bars+pack`（BaoStock d） | **manifest-only**（冻结 pack 缺；raw 缺） | 代码有，**字节缺**（2A.3 DATA_BLOCKED） |
| 分钟 1min/5min | ✅（超短线关键） | **无**（全仓 `frequency="d"`；SESSION「稍后」） | 无 | **代码+字节全缺（NEW）** |
| Level-2/逐笔 | 可选（超短线理想） | **无** | 无 | **全缺（付费，禁采购）** |

## 2. 资金
| 数据 | 需要 | 代码适配器 | Cloud 字节 | 结论 |
|------|------|-----------|-----------|------|
| 主力/个股资金流 | ✅（热点/龙头核心） | **无**（仅 v11 roadmap 提及 TuShare moneyflow） | 无 | **全缺（NEW，多为付费）** |
| 北向 | ✅（曾） | `v38_overlay/global_north` + `sentiment/EM_NORTHBOUND_DAILY.json.gz`（33KB 存在） | 部分（市场级） | **2024-08 港交所停发个股北向 → DATA_BLOCKED（非个股可交易）** |
| 龙虎榜 | ✅（短线核心） | **零代码** | 无 | **全缺（NEW）** |

## 3. 基本面
| 数据 | 需要 | 代码适配器 | Cloud 字节 | 结论 |
|------|------|-----------|-----------|------|
| 财报（季/年） | ✅（融合） | `information_v16`/`findeep_v27`（Eastmoney/BaoStock，下载+编译齐全） | **manifest-only**（raw/npy 缺） | 代码有，字节缺，**未接 A-Short** |
| 业绩预告/快报 | ✅（事件催化） | `preann_v38`（下载+PIT 编译） | **manifest-only** | 代码有，字节缺，未接 |
| 分红/增减持/质押 | 可选 | `div_v21`/`insider_v38`/`pledge_v38` | **manifest-only** | 代码有，字节缺，未接 |
| 行业分类 | ✅（板块轮动） | `information_v16` 行业 PIT（BaoStock 月度） | **manifest-only** | 代码有，字节缺，未接 |
| 市值 | ✅（质量/分层） | **无独立适配器** | 无 | **缺（可由价×股本推，需股本数据）** |
| 融资融券 | 可选 | `margin_v23`（Eastmoney 日频） | **目录整体缺失** | 代码有，字节缺，未接 |
| 户数 | 可选 | `holders_v24` | **manifest-only** | 同上 |
| 指数（HS300/ZZ500 日线 + 成分） | ✅（基准/β/成分） | `index_v20` + `ml_v25/index_daily` | **日线 present**；成分 manifest-only | 部分可用 |

## 4. 政策 / 新闻 / 公告（文本）
| 数据 | 需要 | 代码适配器 | Cloud 字节 | 结论 |
|------|------|-----------|-----------|------|
| 财经新闻 | ✅（热点/情绪） | **无** | 无 | **全缺（NEW，需 NLP+PIT 语料）** |
| 政策（国务院/发改委/央行/行业） | ✅（催化） | **无** | 无 | **全缺（NEW）** |
| 公告（一般文本） | ✅ | **仅 `.gitkeep` 占位** | 无 | **全缺（结构化事件≠文本公告）** |

## 5. 情绪 / 海外 / 宏观 / 汇率 / 商品（叠加层）
| 数据 | 代码 | Cloud 字节 | 结论 |
|------|------|-----------|------|
| 市场情绪（新开户/融资增速/换手/涨停家数） | `v38_overlay/sentiment`（O3）+ `sentiment/*.json.gz` | 小量 present | 有，市场级，未接 A-Short |
| 海外指数（DJI/HSI/N225/IXIC） | Yahoo gz（O4，已 REJECT） | present（小） | 有，未接 |
| 宏观/汇率/商品 | `macro_v17` + `immutable/*` D1 | present（非 A 股） | 有，未接，与个股短线相关性存疑 |

---

## 6. 「09:00 推荐」数据依赖总结
**当前仓库已有（代码层面）**：D1 价格管线、参考表（日历/basics/universe，**字节 present**）、成熟信息层下载+编译代码（融资/户数/财务/行业/指数/预告/增减持/质押/分红）、市场级情绪/北向/海外小缓存、LLM 传输层（fusion/cursor_cloud）、纸面骨架（paper_ops）。

**缺少（NEW，代码+数据都无）**：
1. **分钟/intraday**（超短线关键）
2. **龙虎榜**
3. **个股资金流**（主力/vendor）
4. **新闻/政策/公告文本 + PIT 语料 + NLP**
5. **板块轮动/热点/龙头**衍生层
6. **市值**独立数据

**缺少（有代码但 Cloud 无字节，且未接入 A-Short）**：全部结构化信息层（财务/行业/预告/融资/户数/质押/增减持/指数成分）。

**关键前置阻塞**：冻结 D1 面板字节在 Cloud 不可用（Phase 2A.3 `FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`）——**连最基础的 D1 都跑不了，遑论上层信息/热点/龙头**。

---

## 7. PIT / 治理提醒
- 任何新数据（分钟/龙虎榜/资金流/新闻政策）都须：先查 `A_SHORT_DATA_SOURCE_MATRIX.md` / `SPEC`，登记为**新数据集 + 新适配器 + 新预注册合同**，不改冻结 hash、不采购付费（当前禁止）。
- 新闻/政策做**历史回测**须先建 timestamped 语料（published/captured/knowledge_time/source/content_hash）——实时 LLM 输出≠可回测（见 `A_SHORT_DATA_FLOW_V2.md §4`）。
