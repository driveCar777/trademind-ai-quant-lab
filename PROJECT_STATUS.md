# TradeMind AI Quant Lab — PROJECT STATUS

> **接力开发入口。** 任何 AI 接手项目，先读：`AGENTS.md` → `SPEC.md` → 本文件 → `TODO.md`。

**最后更新：** 2026-09-04 深夜（规则修正 V1；**V25 ML1 = 第一个独立 Level-1 Candidate**；NEW_INDEPENDENT=**1**；Final OOS 待用户解锁）  
**更新人：** Cursor  
**事实以 `docs/TRADEMIND_CONTEXT.md` 为准。** 下文旧勾选表不要当现状。

---

## 一、项目定位

TradeMind 是运行在本地 Jetson 集群上的 AI 量化研究与投研实验平台，由 Windows Master 调度、Worker 执行计算，一人 + AI 长期协作维护。

---

## 二、当前版本

| 项 | 值 |
|----|-----|
| 版本 | **V25 / V25.1 / V26 / V27 / V28 done；V29 ML1 前向管线 Smoke PASS（Stability 进行中）；Amendment V2 + V30 MT5 美股 CFD NO_CANDIDATE（`MT5_STOCK_CFD_COST_CEILING`）**（ML1 Level-1 + 复现 PASS + 策略规格 + Final OOS PASS；V27 季报层 LEVEL1_SAME_CLUSTER_AS_ML1；V22–V24 NO_CANDIDATE；Databento 余额 ≈$46） |
| 状态 | 用户授权修改规则 → `RESEARCH_RULES_AMENDMENT_V1`（A1–A4）。V25：14 个已有 PIT 特征 → 1 个预注册 LightGBM。验证超额 +1.47%/20d（t 17.1），LO20 验证 +30.9%（熊市；CAGR 11.1%，MaxDD −21%），研究 CAGR 14.5%（MaxDD −47%），滚动 5/5，成本 2× 仍正，复现 7/7，placebo 干净，超额序列 corr vs H11 0.06。**NEW_INDEPENDENT=1**。Paper=NO。H11/H12 KEEP_LOW_PRIORITY。 |
| 当前 Phase | **V29 ML1 前向管线（2026-09-05）**：`research_engine/ml1_live/daily.py` 每天拉增量日线/融资/户数/成分 → live pack（冻结块逐位相同）→ 14 特征 → REFIT_240 模型（2025-11-06 已缓存）→ 前 20% 名单 `live/signals/SIGNAL_{date}.json` → 影子账本 `live/ledger/LEDGER.json`（接 V28 链，信号 2026-08-28 已 OPEN，999 只/996 可成交，¥5M 等权，无发单）。冒烟 5/5：2026-07-30 重打分与 V28 分数 Δ0.0。Stability = 连续 5 个交易日 + 第一期结算（≈2026-09-29）→ Freeze。有账户的 Paper 仍待用户。 **前一步 ML1 Final OOS 单次读取 PASS（V28，用户委托，已锁）**：2024-03→2026-07 超额 vs EW +1.00%/20d（t 9.3），LO20 +71.4%（CAGR 24.3%，MaxDD −21%），19/30 期打过 EW；EW 自己 +1.17%/20d（小盘牛市），一半以上是 β。三段正账本 +276% / +30.9% / +71.4%。**下一门 = Paper 准备**（五源每日增量管线 + 打分器只出名单 + 监控账本；先 Design）；Paper 开始需用户。策略规格 `V26_ML1_STRATEGY_SPEC.md` 不变。Portfolio 仍需第二条正袖子。不动 ML1 任何参数。**V27 季报层（$0）已冻**：ML2F 仅季报模型与 ML1 正交（超额 corr 0.06）、验证超额 +0.52% t 5.6、滚动 5/5，但 LO20 验证资金 −0.3% 不过门；ML2 全栈 corr 0.96 同簇、无增量。季报层 = 唯一与 ML1 正交且验证显著的信息层，问题在 20 日多头账本不在信息。 |

---

## 三、目前完成情况

- [x] Worker Template（indicator-worker）— 已冻结
- [x] 项目治理文档框架
- [x] 目录结构
- [x] Master API 骨架（待对齐 SPEC）
- [x] V1.1 技术规范（SPEC.md）
- [x] 项目状态文档（本文件）
- [ ] Master 代码对齐 SPEC
- [ ] Worker 配置对齐 SPEC
- [ ] Smoke Test 01/02/03
- [ ] Xavier Docker 部署验证
- [ ] 端到端验证
- [ ] 稳定性测试（100 次 RSI）
- [ ] V1.1 Freeze

---

## 四、当前唯一开发目标

```
Dashboard / Client → Master /api/v1/ai/* → AI Gateway :9100 → Qwen2.5-14B-Instruct
```

V1.1–V9.0 已冻结。研究 → 先看拟单 → 人手确认。V9：模拟盘才 `order_send`，实盘拒绝。Xavier 只算 Master 给的 close。同花顺未接。

本机启动：`start_all.bat`。Xavier 四台：`start_xavier.bat`（01 Docker，其余 `server.py`）。对照：`docs/DESIGN_XAVIER01.md`。

回测节点对外端口 **8002**（板上 `server.py` 写死），不是 8080。

---

## 五、当前目录结构

```
TradeMind/
├── AGENTS.md
├── SPEC.md
├── PROJECT_STATUS.md
├── master/api/
├── workers/indicator-worker/
├── storage/
├── tests/smoke/
└── config/
```

---

## 六、当前所有模块状态

| 模块 | 状态 |
|------|------|
| Master API | Implement |
| Indicator Worker | Freeze（配置待对齐） |
| Factor Worker | Not Started |
| Backtest Worker | Not Started |
| Dashboard | Not Started |
| SDK | Not Started |

### Implement 总进度

```
Progress: 13% (Phase 1/8 完成)

Master      ██████░░░░  60%
Worker      █████████░  90%
Smoke       ░░░░░░░░░░   0%
Stability   ░░░░░░░░░░   0%
Freeze      ░░░░░░░░░░   0%
```

---

## 七、当前所有规范（详见 SPEC.md）

| 规范 | 摘要 |
|------|------|
| Task 生命周期 | CREATED → RUNNING → COMPLETED / FAILED |
| Worker 生命周期 | OFFLINE ↔ ONLINE |
| Task ID | tm-task-YYYYMMDD-NNNNNN |
| Worker 类型 | indicator-worker |
| API 响应 | {success, message, code, data} |
| 错误码 | TM-0000 / TM-1001 / TM-1002 / TM-1003 |
| Storage | tasks/ 元数据 + results/YYYY/MM/DD/ 结果分离 |

---

## 八、当前已冻结决策

Decision 001–008（V1.0）+ Decision 009–016（V1.1），详见 DECISIONS.md。

---

## 九、当前技术栈

Python 3.8 / FastAPI 0.83.x / Docker / Jetson Xavier NX / Windows Master

---

## 十、部署情况

| 节点 | 组件 | 状态 |
|------|------|------|
| Windows PC | Master API (:9000) | 本地开发 |
| Xavier #1 | indicator-worker (:8000) | 待 Phase 5 验证 |
| Xavier #2–#4 | — | 未部署 |

---

## 十一、测试情况

| 测试 | 状态 |
|------|------|
| Worker 单元测试 | PASS（V1.0） |
| Smoke 01/02/03 | 待 Phase 4 创建 |
| Stability 100x RSI | 待 Phase 7 |

---

## 十二、当前阻塞点

1. Master 代码尚未对齐 SPEC
2. Worker 仍含 master_host / master_port
3. Smoke Test 未建立
4. Xavier Docker 未验证

---

## 十三、下一步

**V9.0 已冻结。** 点「重启调度中心」加载新代码。MT5 芯片拉本机 M15；确认后才发模拟盘。冒烟是假终端，真实终端要你本机开着模拟账户再点。

---

## 十四、Definition of Done（V1.1 Freeze）

| 层次 | 标准 | 状态 |
|------|------|------|
| 功能 | E2E Master → Worker → RSI PASS | 待测 |
| 测试 | Smoke 01/02/03 + 100 次 RSI PASS | 待测 |
| 文档 | 全部治理文档更新 | Phase 1 完成 |

---

## 十五、Phase 完成记录

| Phase | 名称 | 状态 | 完成日期 |
|-------|------|------|----------|
| 1 | 文档同步 | PASS | 2026-07-16 |
| 2 | Master 代码对齐 | 待开始 | — |
| 3 | Worker 配置对齐 | 待开始 | — |
| 4 | Smoke Test | 待开始 | — |
| 5 | Xavier 部署 | 待开始 | — |
| 6 | 端到端验证 | 待开始 | — |
| 7 | 稳定性测试 | 待开始 | — |
| 8 | Freeze 文档更新 | 待开始 | — |
