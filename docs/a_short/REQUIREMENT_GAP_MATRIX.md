# REQUIREMENT_GAP_MATRIX.md

> 需求 × 当前状态 × 文件证据。状态：✅ Implemented（A-Short 已实现）· 🟡 Partial（存在但未接入 A-Short / Cloud 无字节）· ❌ Missing（无代码）。

| # | 需求 | 当前状态 | 文件证据 |
|---|------|----------|----------|
| 1 | 每日推荐股票 | 🟡 Partial | A-Short 无 live 出单；`baseline.top_k_period` 仅离线 Top-K；ML1 出单在 `ml1_live/shortlist.py`（未接 A-Short） |
| 2 | 热点分析 | ❌ Missing | 无代码 |
| 3 | 下一波热点预测 | ❌ Missing | 无代码 |
| 4 | 龙头股票识别 | ❌ Missing | 无代码 |
| 5 | 涨停分析 | 🟡 Partial | `cn_a_share_ml_v33/run.py::limit_up_matrix`（D1 派生，**独立冻结，不属 A-Short**） |
| 6 | 政策分析 | ❌ Missing | 无政策文本/NLP（仓库级 DATA_BLOCKED） |
| 7 | 宏观分析 | 🟡 Partial | `cn_a_share_macro_v17`（immutable 宏观叠加，**未接 A-Short**） |
| 8 | 新闻分析 | ❌ Missing | 无（`announcements/` 仅 `.gitkeep`；`factors/space.py` NEWS=DRAFT） |
| 9 | 资金流 | ❌ Missing | 无个股资金流适配器；北向 `sentiment/*.json.gz`（市场级，2024-08 停发） |
| 10 | 龙虎榜 | ❌ Missing | **全仓零代码零数据** |
| 11 | 基本面 | 🟡 Partial | `cn_a_share_information_v16`/`findeep_v27`（下载+编译有，**未接**，Cloud manifest-only） |
| 12 | 技术面 | 🟡 Partial（极弱） | 仅 20D 动量 `baseline.momentum_scores`；`indicator-worker`（RSI 等）不进 A-Short |
| 13 | 股票历史行为分析 | 🟡 Partial | `baseline` 用 D1 open/close/vol/amount/turn，仅动量利用 |
| 14 | 因子挖掘 | ❌ Missing | 无因子库/IC/正交化（`research_engine/discovery` 非 A-Short） |
| 15 | 模型预测 | 🟡 Partial | A-Short 仅动量；ML1（LightGBM REFIT_240）成熟但**未接** |
| 16 | GUI | ❌ Missing | 仅 4 个 HTML（ML1/hot，`dashboard/*.html`）；无 PySide6/A-Short 页面 |
| 17 | Windows 通知 | ❌ Missing | 仅网页内 toast；无 OS toast/winotify/scheduler |
| 18 | 模拟交易 | 🟡 Partial | `baseline.top_k_period` 离线撮合；ML1 `paper_ops`（未接 A-Short）；无 A-Short live 账本 |
| 19 | 资金管理 | ✅/🟡 | `cn_a_short/account.py` 算术可行性（✅）；live 资金管理未实现（🟡） |
| 20 | 账户记账 | 🟡 Partial | ML1 journal→账户在 `paper_ops.derive_account`（未接 A-Short）；A-Short 无 live 账户 |

---

## 汇总
| 状态 | 计数 |
|------|------|
| ✅ Implemented | 1（资金管理·算术） + baseline/成本/撮合/评估引擎 |
| 🟡 Partial（未接/无字节） | 10 |
| ❌ Missing（无代码） | 9 |

**读法**：20 项需求里 A-Short 真正实现的只有「20D 动量 + 撮合/成本/账户/评估引擎」。「Partial」不是"快好了"——接入需先解冻数据、逐层新预注册合同、再做融合/执行/GUI/通知工程。**Missing 的 9 项（热点/龙头/新闻/政策/龙虎榜/资金流/因子/GUI/通知）连代码都没有。**
