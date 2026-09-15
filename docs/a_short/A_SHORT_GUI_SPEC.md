# A_SHORT_GUI_SPEC.md

> 桌面 GUI 设计（§45–52）。技术栈 PySide6/Qt6。定位：**Operator Console / Visualization Layer**——可视化 + 手动触发 + 设置，
> **不承载**采集/调度/LLM/推荐/记账（§8）；**可关闭而后台继续**（§9）；**只读 · 不发单**（§10）。

---

## 1. 与后台的契约（零后端耦合）

- GUI 只通过 localhost HTTP(JSON) 读后台 `:9002`，沿用现有 `dashboard/paper.html` 的 **poll-only** 模式（每 8–120s 拉一次；运行中 8s，空闲 120s）。
- 所有「立即更新/重算」按钮 = `POST /api/v1/ashort/*` 触发后台**同一** pipeline（§25），GUI 不含业务逻辑。
- 断连/后台未起：GUI 显示「后台离线」并给「启动后台」按钮（调 `start_all.bat` 式健康检查再启，不双开）。

**可复用视觉底座**：`cursor/ashare-desktop-gui-3072` 分支已有一个 PySide6 深色壳（`theme.py` QSS、`widgets.py` 的 `Card/KpiCard/LiveDot/Sidebar/FadeStack`、count-up/侧栏滑块/淡入动画）。A-Short GUI 可**复用该主题与组件**，替换数据层为 `:9002` 契约。该壳当前是 ML1 纸面台的只读展示，与 A-Short 并行、不冲突。

---

## 2. 页面清单（§46）

`Dashboard · Market · Themes · Leaders · Stocks · News · Policy · Portfolio · Recommendations · Research · Data Health · Scheduler · Logs · Settings`

分组（侧栏）：
- **今日**：Dashboard, Recommendations, Portfolio
- **市场**：Market, Themes, Leaders, Stocks
- **信息**：News, Policy
- **系统**：Data Health, Scheduler, Logs, Research, Settings

> 第一阶段落地优先级：Dashboard → Recommendations → Portfolio → Data Health → Scheduler → Settings；Market/Themes/Leaders/News/Policy 依赖 NEW 数据，按数据到位分批。

---

## 3. 首页 Dashboard（§45）

一屏速览（卡片网格）：
```
A-SHORT              [状态灯: RUNNING/NO_EDGE/DATA_FAILED]   Last Update 08:47
┌ Market Opportunity 0.91 ┐ ┌ Market Regime  TREND_HI_MIDVOL ┐ ┌ Data Health 94% ┐
│ S:4  A:17  B:63         │ │ breadth ↑ / 涨停 62 / 换手 z+1.2│ │ Price✓Cal✓News⚠ │
└─────────────────────────┘ └────────────────────────────────┘ └─────────────────┘
┌ Top Themes ──────────┐ ┌ Emerging Themes ─┐ ┌ Top Leaders ─────┐
│ AI ↑↑↑ Robot ↑↑ ...  │ │ 低空经济 ↑ ...    │ │ 600xxx 600yyy ... │
└──────────────────────┘ └──────────────────┘ └──────────────────┘
┌ Top Opportunities (Top 3~15) ── T+1/T+3/T+5 期望/风险/WHY/矛盾 ──┐
│ #1 sh.600xxx  S  T+1 +3.2%  Quant .88 Info .82  可执行✓  WHY... │
└─────────────────────────────────────────────────────────────────┘
┌ Paper Account: equity ¥xx  cash ¥xx  持仓 n  今日操作: SELL 2 / BUY 3 ┐
Scheduler State: 08:58 冻结完成 · 09:00 已通知 · 下次 06:30
```
- **NO TRADE 合法**：Opportunity 低时首页明确显示 `NO_EDGE` + 原因（§20），不硬凑交易。

---

## 4. 推荐详情 Recommendations / 股票详情（§47、§56）

每条推荐可展开为股票详情页：
```
Stock sh.600xxx  [Recommendation: S]
T+1 +3.2%(p .71)  T+3 +5.1%  T+5 +6.4%     Quant .88 / Info .82 / Data 96% / Executable YES
Theme: AI 算力 (leader)   Leader State: 龙一   Behavior Fingerprint: 放量突破
Capital Flow: 融资净买入↑   Fundamental: 预告预增   Policy: 数据要素   News: [证据ID...]
Bull Case ▸ ...    Bear Case ▸ ...    Contradictions ▸ priced_in? narrative?
Historical Analogs ▸ 近似形态 5 例, 平均 T+3 +4.1%
Evidence ▸ 追溯链: Fusion→Model→Features→Theme→Leader→News→Policy→Raw
```
- 双可信度 **Quant Confidence / Information Confidence** 分列（§56），外加 `Data Completeness / Executable`。
- 「可执行」由 Portfolio 层给出，与 Alpha 分离（§15）。

---

## 5. 图表（§48）

| 区 | 图 |
|----|----|
| Market | 指数、breadth、涨停/跌停、市场成交额 |
| Theme | strength / acceleration / breadth / flow（Theme Heatmap，§50） |
| Stock | K 线 + 量 + 涨停事件标记 + behavior fingerprint + 主题关系 + 预测带 |
| Paper | equity curve / drawdown / cash / exposure / 月度表现 / contribution / withdrawal |

Theme/Capital 关系用 Heatmap + 分层图（Theme↕Industry↕Leader↕Stock，§50）。图表库：Qt 原生 `QtCharts` 或 `pyqtgraph`（后者更快，适合 K 线/大数据）。

---

## 6. 动画（§49）——克制，不牺牲信息密度

允许：主题强度变化、龙头排名变化、新推荐出现、资金流变化、纸面账户变化的**过渡动画**（数值 count-up、排名条滑动、卡片淡入、状态灯脉冲）。
底座已有：`KpiCard` count-up、`Sidebar` 滑块、`FadeStack` 淡入、`LiveDot` 脉冲。
禁止：为炫技牺牲信息密度（§49）；大面积粒子/视差。

---

## 7. 通知（§20、§51；Phase 1.1 修订：GUI 不是发送方）

> **修正**：通知发送归**后台 Notification Service**（Decision A-004），**不依赖 GUI**——`QSystemTrayIcon.showMessage()` 需 Qt 事件循环，弃用作后台通知。GUI 只**读通知历史**（`NOTIFICATIONS.json`）。无 GUI 发送方案（winotify / PowerShell WinRT）、用户会话约束、dedupe/quiet-hours/错过重放，详见 **[A_SHORT_NOTIFICATION_SPEC.md](A_SHORT_NOTIFICATION_SPEC.md)**。GUI 关闭时 Windows 通知**仍工作**。

- 渠道：**仅 Windows 通知**（后台直发）。不做 TG/微信/邮件（除非后续明确）。
- 09:00 若有推荐：极简 toast
  ```
  TradeMind A-Short
  今日发现 7 个高质量机会。Top 3 已生成。点击查看。
  ```
- 0 强候选：可不发交易提醒；但 GUI 内显示 `NO_EDGE` + 原因。
- 完整信息只在 GUI（通知不塞分析）。dedupe/quiet-hours/错过重放见 [Scheduler 文档](A_SHORT_SCHEDULER_SPEC.md)。

---

## 8. 设置页（§52、§53）

分区：
- **Account**：initial capital / max capital / contribution on-off·freq·amount / withdrawal。
- **Research**：universe / boards / liquidity / max price / strategy switches。
- **Scheduler**：timezone(Asia/Shanghai) / market_open·close / data_refresh_time / analysis_start / analysis_deadline / notification_time（§22，全部可配，不写死）。
- **AI**：API model（下拉，禁手输，仿 gateway 目录）/ prompt versions / token budget·concurrency。

**每个参数必须显式标注影响层（§53）**：
```
[Alpha]   Research universe 改变  → 可能重算 signal
[Portfolio] Capital / max capital 改变 → 只改可执行组合, 不重算 alpha
```
改 Account 参数**绝不**触发 alpha 重算；改 Research universe 才可能触发 signal 重生成。

---

## 9. 托盘 / 窗口生命周期（NEW）

- 关闭主窗 = 最小化到系统托盘（后台服务不受影响）；托盘菜单：打开面板 / 立即更新 / 今日推荐 / 退出后台。
- 单实例（防双开 GUI，仿 `start_all.bat` 健康检查）。
- GUI 未开时 09:00 通知：由后台记「待送」，下次 GUI 起来补一条「今晨 09:00 有推荐」；或后台侧用 Windows 通知中心 API（评估）。

---

## 10. 治理（Phase 1.1 已批准）

AGENTS.md V1.1「禁 Qt 前端」已由 **Decision A-002** 条件批准：PySide6 桌面 GUI 允许，条件 = 独立进程 / 只读+控制台 / 不发单 / 无策略逻辑 / 无数据层 / 后台 localhost:9002 / 关 GUI 不停后台。见 [A_SHORT_GOVERNANCE_DECISIONS.md](A_SHORT_GOVERNANCE_DECISIONS.md)。
