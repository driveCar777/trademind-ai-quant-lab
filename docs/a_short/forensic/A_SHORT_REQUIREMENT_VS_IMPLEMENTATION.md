# A_SHORT_REQUIREMENT_VS_IMPLEMENTATION.md

> 需求 × 当前状态 × 缺失。状态取自代码事实（非文档）。图例：❌ 无代码 · 🟡 有相邻代码但未接入 A-Short · 🟢 A-Short 已实现。

| 需求 | 当前状态 | 缺失 |
|------|----------|------|
| 热点发现 | ❌ 无 | 题材/概念聚类、热度指标、数据源全缺 |
| 板块轮动 | ❌ 无 | 行业/板块收益动量、轮动信号；行业数据仅 manifest（Cloud 无字节） |
| 龙头识别 | ❌ 无 | 板块内相对强度/领涨识别，全缺 |
| 涨停分析 | 🟡 相邻 | `cn_a_share_ml_v33::limit_up_matrix`（D1 派生）存在但**冻结独立、不属 A-Short**；A-Short 无涨停/连板建模 |
| 龙虎榜 | ❌ 无 | **整仓库零代码零数据**；文档标 NEW |
| 资金流 | ❌ 无 | 主力/个股资金流无适配器；北向 gz 缓存存在但**2024-08 停发**、且非个股级可交易 |
| 公告 | ❌ 无 | `announcements/` 仅 `.gitkeep`；结构化事件（分红/预告/增减持）有包但未接入且 Cloud 无字节 |
| 政策 | ❌ 无 | 政策文本/NLP 全缺（仓库级 DATA_BLOCKED/forbidden） |
| 宏观 | 🟡 相邻 | `cn_a_share_macro_v17` 用 immutable 宏观叠加，**未接入 A-Short** |
| 海外市场 | 🟡 相邻 | `sentiment/raw` 有 Yahoo DJI/HSI/N225/IXIC gz；O4 全球联动已判 REJECT；**未接入 A-Short** |
| 汇率 | 🟡 相邻 | `data/market/immutable` 有 FX D1；**未接入 A-Short** |
| 大宗商品 | 🟡 相邻 | immutable 有商品 D1 + cn_futures 包；**与 A-Short 短线选股无关，未接入** |
| 技术指标 | 🟡 相邻 | 独立 `indicator-worker`（RSI 等）存在，**不进 A-Short**；A-Short 打分只有 20D 动量 |
| 个股历史行为 | 🟢 部分 | `baseline` 用 D1 open/close/vol/amount/turn；仅动量利用，其余字段未成特征 |
| 因子挖掘 | ❌ 无 | 无因子库/正交化/IC 框架（其它包有 discovery，但非 A-Short） |
| 机器学习 | 🟡 相邻 | ML1（LightGBM REFIT_240）成熟，**A-Short 未接**；A-Short 无 ML |
| LLM 辅助 | 🟡 相邻 | `paper_fusion` + `cursor_cloud`（Grok 层）成熟，**A-Short 未接** |
| GUI | ❌ 无 | 仅 4 个 HTML（ML1/hot）；无 PySide6/`ashare-desktop`/A-Short 页面 |
| 通知 | ❌ 无 | 仅网页内 toast；无 OS toast/winotify/`NOTIFICATIONS.json`/scheduler |
| 纸面交易 | 🟡 相邻 | `paper_ops`(1294行)/`paper_service` 成熟（ML1 用）；**A-Short 未接**；`cn_a_short.baseline` 有离线撮合但非 live 账本 |
| 账户管理 | 🟡 相邻 | ML1 paper 有 journal→账户派生；A-Short 无 live 账户（`account.py` 仅算术可行性） |

---

## 汇总
| 类别 | 计数 |
|------|------|
| 🟢 A-Short 已实现 | 1（个股历史行为·部分） + 引擎/成本/账户算术 |
| 🟡 有相邻代码但未接入 | 9（涨停/宏观/海外/汇率/商品/技术指标/ML/LLM/纸面·账户） |
| ❌ 完全无 | 11（热点/板块/龙头/龙虎榜/资金流/公告/政策/因子/GUI/通知） |

**读法**：目标 21 项里，A-Short 真正落地的只有「20D 动量 + 撮合/成本/评估引擎」。**「相邻但未接入」不是"快好了"**——接入这些（尤其信息层）还需：Cloud 拿到 bytes（Phase 2A.3 判 DATA_BLOCKED）、每个信息层新预注册合同、以及新的融合/执行/GUI/通知/scheduler 工程。
