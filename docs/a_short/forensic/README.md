# A-Short 全仓库 Forensic Audit（docs/a_short/forensic/）

> 阶段：**Audit → Architecture Review → Gap Report**（只审计，不开发、不改合同、不调参、不换源、不跑不存在的数据、不宣称 alpha）。
> 只新增本目录文档；未改冻结合同 / ML1 / V33 / 数据 hash / execution 路径。证据来自逐文件代码审计（见各文档的具体路径与函数名）。

---

## BAD NEWS FIRST（先说坏消息，不弱化）

1. **实现与目标严重脱节。** 目标是「中国 A 股短线/超短线 + 基本面技术面融合 + 政策/资金/热点驱动 + 板块轮动 + 龙头 + 涨停/连板/龙虎榜/资金流/公告/政策 + 每日纸面推荐 + GUI + Windows 通知 + 模拟账户」。**当前 A-Short 实际实现 = 一个离线的 D1 回测引擎 + 唯一打分 = 20 日动量**，其余全部未实现。
2. **连"短线"都不成立。** 唯一实现的打分是 `momentum_scores(lookback=20)`——**20 日回看动量**，是中周期信号，**方向上就不是短线**。合同特征族（reversal/gap/量能/换手/波动/breadth/涨停计数）**仅 specified，零实现**。
3. **没有热点/板块/龙头/涨停/龙虎榜/资金流/公告/政策/宏观/海外/汇率任何一个信息层进入 A-Short 运行链路。** 这些数据里，龙虎榜/资金流/新闻政策文本/分钟数据**在整个仓库都没有代码实现**；其余信息层（融资/户数/财务/行业/指数/预告/增减持/质押）**有下载+编译代码**，但 A-Short **没有接入**，且本 Cloud checkout **只有 manifest，无实际字节**。
4. **A-Short 与现有 live 管线是平行的，没有复用。** `cn_a_short` **不 import** `ml1_live` / `paper_ops` / master api——它是独立离线研究包，不是短线系统的运行时。
5. **GUI / Windows 通知 / Scheduler / :9002 后端 = 100% 文档，零代码。** 仓库里没有 PySide6、没有 `ashare-desktop`、没有 OS 级 toast、没有 `NOTIFICATIONS.json`、没有任务计划注册脚本。现有 GUI 只有 4 个 HTML（ML1/hot 用），通知只有网页内 toast。
6. **数据在 Cloud 不可用。** 冻结 D1 面板字节 `REGISTERED_BUT_BYTES_UNAVAILABLE`（Phase 2A.3 已判）；所有 bulk 信息层同样 gitignored/manifest-only。→ **当前 A-Short 无法跑任何真实 empirical alpha。**
7. **天然偏向垃圾股。** ALL universe（含 ST/微盘/低价/科创/创业/北交所）+ 20D 动量 + 无质量过滤 ⇒ Top-K 天然偏 LOW_PRICE/SMALL_CAP/HIGH_VOL/ILLIQUID（详见 `CURRENT_UNIVERSE_REPORT.md`）。这是设计特征，不是 bug，但意味着任何 Top-K 表现须先归因于小盘 β。

---

## 结论一句话
A-Short **当前是「A：一个简单动量回测脚手架」**；架构文档朝「D：AI 辅助投资研究平台」设计；而**需求本质是「C：短线热点交易系统」融合「D」**。三者之间是**数量级的实现缺口**，不是调参能补的。**Phase 2B 现在不能开始**（详见 `A_SHORT_NEXT_DECISION.md`）。

---

## 文档清单
| 文件 | 内容 |
|------|------|
| [A_SHORT_CODE_INDEX.md](A_SHORT_CODE_INDEX.md) | 代码索引：路径/功能/输入/输出/依赖/是否进入 A-Short 运行链路 |
| [CURRENT_UNIVERSE_REPORT.md](CURRENT_UNIVERSE_REPORT.md) | 当前股票池与 eligibility 真相 + 是否偏向垃圾股 |
| [CURRENT_MODEL_REALITY.md](CURRENT_MODEL_REALITY.md) | 当前模型现实：Specified / Implemented / Missing |
| [A_SHORT_REQUIREMENT_VS_IMPLEMENTATION.md](A_SHORT_REQUIREMENT_VS_IMPLEMENTATION.md) | 21 项需求 × 当前状态 × 缺失 |
| [A_SHORT_DATA_ARCHITECTURE_REVIEW.md](A_SHORT_DATA_ARCHITECTURE_REVIEW.md) | 每日 09:00 推荐所需数据：已有 vs 缺失 |
| [A_SHORT_DIRECTION_AUDIT.md](A_SHORT_DIRECTION_AUDIT.md) | 是否走偏（A/B/C/D）+ 原因 |
| [A_SHORT_NEXT_DECISION.md](A_SHORT_NEXT_DECISION.md) | Phase 2B 是否开始 + 先补什么 |

### Observability / Forensic 基础设施（Audit + Design，未实现代码）
| 文件 | 内容 |
|------|------|
| [CURRENT_OBSERVABILITY_AUDIT.md](CURRENT_OBSERVABILITY_AUDIT.md) | 现有 logging/artifact/report 能力审计：已有/缺失/推荐最小实现/风险 |
| [A_SHORT_OBSERVABILITY_DESIGN.md](A_SHORT_OBSERVABILITY_DESIGN.md) | 观测层总设计（runs/RUN_ID 布局 + 4 个新增快照/归因/分类） |
| [A_SHORT_RUN_MANIFEST_SPEC.md](A_SHORT_RUN_MANIFEST_SPEC.md) | Run Manifest 规范（代码/数据/模型/成本/执行 版本 + 复现 hash） |
| [A_SHORT_TRADE_FORENSIC_SPEC.md](A_SHORT_TRADE_FORENSIC_SPEC.md) | SIGNALS 快照 + 交易生命周期状态机取证 |
| [A_SHORT_FAILURE_DIAGNOSIS.md](A_SHORT_FAILURE_DIAGNOSIS.md) | 错误分类（DATA/MODEL/EXECUTION/COST/ENV）+ 判定信号 |
| [A_SHORT_EXPERIMENT_REPORT_SPEC.md](A_SHORT_EXPERIMENT_REPORT_SPEC.md) | 自动 REPORT.md（11 节，含"为什么不赚钱"） |

> 状态：本轮仅 **Audit + Design（docs only）**。Minimal Implementation（`cn_a_short/forensic/` + 接线 + 测试）= Phase 3，待确认后进行。

> 原始审计证据来自两个只读子代理扫描：master/api + ai-gateway + dashboard + GUI + ml1_live/ml7_live；以及 research_engine 全部 A-share 数据适配器与磁盘落地情况。
