# A_SHORT_NOTIFICATION_SPEC.md

> 通知设计（§5、§18、Decision A-004）。**通知与 GUI 彻底解耦**：后台不依赖 GUI 也能发 09:00 Windows 通知。
> 修正 Phase 1 的错误（把通知放在 `QSystemTrayIcon.showMessage()`，需 Qt 事件循环 = GUI 必须开）。

---

## 1. 架构（GUI 不是发送方）

```
Scheduler / Backend (:9002)
        │  (今日是否有推荐 / 系统是否失败)
        ▼
Notification Service   ── 写 NOTIFICATIONS.json (真相/历史)
        │
        ▼
Windows Toast  (无需 GUI 运行)
        ▲
        │ (只读)
      GUI  ── 观察通知历史，不发送
```
- **真相源 = `live/ashort/NOTIFICATIONS.json`**（每条：`id/ts/kind/title/body/run_id/dedupe_key/sent_channel/state`）。
- GUI 只读该文件显示「通知历史」；**GUI 关闭不影响发送**。

---

## 2. 无 GUI 的 Windows Toast 发送方案（评估）

| 方案 | 依赖 | 无 GUI | headless 会话 | 评价 |
|------|------|--------|---------------|------|
| **`winotify`（python，包装 WinRT）** | pip 纯 python，无 admin | ✓ | 需**交互用户会话**（非 session 0） | **推荐主用**（零 GUI、注册 AppUserModelID `TradeMind.AShort`） |
| PowerShell + `Windows.UI.Notifications`（WinRT ToastNotificationManager） | 系统自带 PowerShell | ✓ | 同上 | **推荐 fallback**（无 pip 依赖，脚本发） |
| BurntToast PowerShell 模块 | 需 `Install-Module` | ✓ | 同上 | 备选（需装模块） |
| `win11toast` / `plyer` | pip | ✓ | 同上 | 备选 |
| ~~`QSystemTrayIcon.showMessage`~~ | PySide6 + **运行中的 GUI** | ✗ | — | **弃用作后台通知**（仅 GUI 开着时的补充提示） |

**关键约束（写清楚，避免踩坑）**：WinRT toast **必须在交互式用户会话**里弹出。若后台用 **Windows 服务（session 0）** 运行，toast 不显示。
→ **因此 09:00 通知步骤由 Windows 任务计划在“用户已登录会话”下触发**（`ONLOGON`/用户级任务），而非 session 0 服务；后台数据/分析可在服务里跑，但**发 toast 的动作走用户会话的 notify 端点/任务**。详见 [A_SHORT_SCHEDULER_SPEC.md](A_SHORT_SCHEDULER_SPEC.md) §7。

**依赖决策**：`winotify` 是 A-Short 的**新 pip 依赖**（很小，纯 python），需在 Phase 2 requirements 记一行；fallback 用系统 PowerShell 无新依赖。用户未登录时无法弹 toast → 落 `NOTIFICATIONS.json` 待登录后由 GUI/下一 notify 任务补送（见 §5 错过重放）。

---

## 3. 通知语义（§18）

| 情形 | 09:00 toast | GUI 显示 | state |
|------|-------------|----------|-------|
| **有推荐** | 发（极简：`今日 N 个机会，Top 3 已生成，点击查看`） | 完整推荐 | `RECOMMENDATION_READY` |
| **无强机会（真 NO_EDGE）** | **不发**交易 toast | `NO_EDGE` + 原因 | `NO_EDGE` |
| **系统失败** | 发失败提醒（可配）**且不得伪装成 NO_EDGE** | 显式失败态 | `SYSTEM_FAILED / DATA_FAILED / LLM_PARTIAL / PIPELINE_FAILED` |

- **失败 ≠ NO_EDGE**（§18 硬要求）：核心数据失败/管线失败必须以失败态呈现，绝不静默当「今天没机会」。
- 通知只负责**提醒**，不塞完整分析（§51）；完整信息在 GUI。

---

## 4. 幂等 / dedupe / quiet-hours

- **dedupe_key = `{date}:{kind}`**：一天同类通知只发一次；服务 09:04 才重启也只补一次（查 `NOTIFICATIONS.json`）。
- **quiet-hours**：非交易日/夜间不发交易 toast（可配）。
- 失败通知与推荐通知是不同 `kind`，各自 dedupe。

---

## 5. 错过窗口重放（missed notification）

- 机器休眠/关机/未登录 → 错过 09:00：
  - `NOTIFICATIONS.json` 标 `pending`；
  - 下次用户登录 / GUI 启动 / 下一 notify 任务命中时，检测「今日有推荐且未成功送达」→ 补送一条「今晨 09:00 有推荐」，`dedupe_key` 保证不重复轰炸。
- 补送有时效（如超过当日交易时段则降级为 GUI 内提示，不再 toast）。

---

## 6. 与 run_id / 审计对齐

每条通知带 `run_id`，可回溯到当日 `RECOMMENDATION_{date}.json` 与 pipeline 日志（Run Audit，§54）。通知发送成功/失败/补送都记 `sent_channel`（winotify/powershell/gui/deferred）。
