# A_SHORT_SCHEDULER_SPEC.md

> 调度设计（§20–27）。原则：**OS 调度，服务保持幂等**——不加进程内调度库（契合 AGENTS.md「禁 Cron/APScheduler/Timer」），
> 用 Windows 任务计划 + `curl POST` 幂等端点（SPEC §29.11a 已认可的既有模式）。
> 复用锚点：`scripts/hot_fusion_session.bat` + `TradeMind_HotFusion*` 任务；`paper_fusion_fill.py`（会话闸/typed skip/线程自愈/`_now()` 可测）；`paper_ops.py`（独占锁/孤儿恢复/`asof_bogus`）。

---

## 1. 调度模式（不加库）

```
Windows 任务计划 ──curl POST──▶  /api/v1/ashort/session  (幂等)
   TradeMind_AShort_Macro   06:30
   TradeMind_AShort_Info    07:00, 08:00
   TradeMind_AShort_State   08:20
   TradeMind_AShort_Theme   08:30
   TradeMind_AShort_Cand    08:40
   TradeMind_AShort_LLM     08:45
   TradeMind_AShort_Red     08:52
   TradeMind_AShort_Fuse    08:56
   TradeMind_AShort_Freeze  08:58   → RECOMMENDATION_FREEZE
   TradeMind_AShort_Notify  09:00   → 有推荐则 toast
```
- 每个任务跑 `scripts/ashort_session.bat <phase>` → `curl -s -m 30 -X POST http://127.0.0.1:9002/api/v1/ashort/session -d '{"phase":"<phase>"}'`，追加日志。
- **时间是设计目标，非硬编码**（§21）。最终时刻由后台结合数据源延迟/API latency/刷新时间/交易时段/网络可靠性给出，并**全部落 `config/ashort.yaml`**、GUI 可改（§22）：
```yaml
timezone: Asia/Shanghai
market_open: "09:30"
market_close: "15:00"
data_refresh_time: "06:30"
analysis_start: "08:20"
analysis_deadline: "08:58"    # 推荐冻结不得晚于此
notification_time: "09:00"
```

---

## 2. 推荐不能过早（§21）

- 禁止「凌晨算完第二天推荐一直等」。最终冻结尽量贴近 09:00（`analysis_deadline` 08:58）。
- 分阶段增量更新（宏观 06:30 → 政策/新闻 07:00–08:20 → 市场态 08:20 → 主题/龙头 08:30 → 候选 08:40 → LLM 08:45 → 红队 08:52 → 融合 08:56 → 冻结 08:58），每阶段只在前一阶段产物就绪时推进；缺数据的阶段降级并标 `DEGRADED`。

---

## 3. 自动与手动同一 pipeline（§24、§25）

- GUI 手动按钮（立即更新全部数据 / 更新行情 / 新闻 / 政策 / 宏观 / 海外 / 资金 / 重算市场态 / 重生成候选 / 重跑分析 / 重生成今日推荐）→ 同样 `POST /api/v1/ashort/session`（或 `/refresh/<source>`），进入**同一** pipeline，**不复制两套代码**（§25）。
- **手动不绕过 PIT**（§24）：PIT 门在 pipeline 内部，与触发者无关；用户点按钮也不能用未来数据。

---

## 4. 幂等（§23）——复用 `paper_fusion_fill` 会话闸

会话结果枚举（每日每 phase 唯一，落 `ASHORT_SESSIONS.json`，90 天保留）：
```
RAN / SETTLE_ONLY / SKIPPED_NOT_TRADING_DAY / SKIPPED_ALREADY_DONE
/ SKIPPED_STALE_DATA / SKIPPED_RUN_IN_PROGRESS / SKIPPED_NO_CAPACITY / FAILED
```
- **今天该 phase 已完成 → 再触发是 no-op**（`SKIPPED_ALREADY_DONE`）；`_record_session` **绝不用后来的 skip 覆盖已 `RAN`** 记录。
- **单实例**：独占创建 `CURRENT.json`（`O_CREAT|O_EXCL`）；pid 活但 cmdline 读不到时**不拆锁**；无锁的孤儿 `ashort` 进程视为仍在跑（`_find_daily_pids` 同款）。
- 数据陈旧 → `SKIPPED_STALE_DATA`（不拿旧数据出推荐）。
- **不重复执行 Paper Trade**：同一 `recommendation_id` 的纸面执行只落一次（幂等键）。

---

## 5. 失败处理与恢复（§26、§23）

| 场景 | 行为 | 复用 |
|------|------|------|
| 单源失败 | 该源 `STATUS=FAILED/PARTIAL`，记 `LAST_SUCCESS/RETRY_COUNT/LATENCY/COVERAGE/FRESHNESS`（§26），核心失败→停推荐（§27），非核心→降级（§28） | `data_sources/registry` EXTEND |
| 源限流/黑名单 | 退避（`--skip-fetch` 式），greps 近 8 日日志 120 分钟内黑名单则降级 | `paper_ops._recent_baostock_blocked` |
| 进程被杀 | 无 STATUS → `freshness` 用 `asof_bogus/calendar_stale` 兜底；truncated calendar 修复 | `paper_ops._repair_live_calendar` |
| 后台重启 | `pending` 锁 <30s=启动中；旧无 pid=归档为中断；活 pid cmdline 不匹配=归档释放；无锁活进程=重建锁 `recovered` | `paper_ops.run_status` |
| 线程僵死 | `running` 标志自愈（进程重启后可再跑） | `paper_fusion_fill.daily_state` |
| 重试 | 每源指数退避（4/8/16/32s），最多 N 次 | `session.py` 退避 |
| 可测 | 所有时间判断走 `_now()`，可 monkeypatch 09:00 而不等墙钟 | `tests/smoke/22_paper_ops.py` 模式 |

---

## 6. 09:00 通知（§20；Phase 1.1 修订）

> **通知发送由后台 Notification Service 直发，不依赖 GUI**（Decision A-004）。**关键约束**：Windows WinRT toast 必须在**交互式用户会话**弹出——因此 **notify 步骤（09:00 / pre-open / exec）由用户级任务计划触发**（`ONLOGON` + 定时），数据/分析可在服务里跑，但发 toast 走用户会话端点。方案（winotify / PowerShell WinRT）、dedupe、错过重放见 [A_SHORT_NOTIFICATION_SPEC.md](A_SHORT_NOTIFICATION_SPEC.md)。

- 09:00 任务命中 → 后台判「今日是否有推荐」：有 → 发极简 toast；0 强候选（真 NO_EDGE）→ 可不发交易提醒，但 GUI 显示 `NO_EDGE`+原因；**系统失败 → 不得伪装成 NO_EDGE**，发失败提醒并以失败态呈现（§18）。
- **通知幂等**：一天只发一次；服务 09:04 才重启也只补发一次（`ASHORT_SESSIONS.json` 记 `notify:sent`）。
- **错过窗口重放**：机器休眠/关机错过 09:00 → 下次唤醒/GUI 起来时检测「今日未通知且有推荐」→ 补一条「今晨有推荐」，不重复轰炸（dedupe + quiet-hours）。

---

## 7. 系统重启后自动恢复（§23）——方案选型（第一阶段只给方案，不定死）

现状（审计）：仓库**无** Windows 服务/开机自启/任务注册代码；现有任务是手建。候选机制：

| 机制 | 开机恢复 | GUI 不开也跑 | 崩溃恢复 | 不重复 | 可观察 | 评价 |
|------|----------|--------------|----------|--------|--------|------|
| **任务计划 `ONLOGON`+`ONSTART` 拉起后台服务** | ✓（登录/开机） | ✓ | 配「失败重启」 | 单实例锁 | 任务历史+日志 | **推荐起步**（零依赖，契合既有模式） |
| Windows 服务 / NSSM 包装 | ✓（无需登录） | ✓ | 服务自动重启 | 服务单实例 | 服务状态 | 更稳，但需装 NSSM/权限 |
| 托盘 agent 常驻 | ✗（需登录且手动） | ✗ | 弱 | — | 弱 | 不单独用 |

- **推荐组合**：任务计划 `ONSTART`（或 `ONLOGON`）拉起 `:9002` 后台服务（带健康检查，仿 `start_all.bat` 不双开）；各 phase 任务照常 curl。后台崩溃 → 任务计划「若已停止则重启」+ 下一 phase 任务自然重新拉起。
- **上一次任务结果可恢复**：`STATUS.json`（增量写）+ `runs/HISTORY.json` + `ASHORT_SESSIONS.json`。
- 需 NEW：`scripts/register_ashort_tasks.ps1`（幂等注册任务，避免手建）+ `scripts/ashort_service.bat`（健康检查后启动）。

---

## 8. 可观察性

- Scheduler 状态页（GUI §46）显示：各 phase 今日结果（`RAN/SKIPPED_*/FAILED`）、下次触发时间、上次 `run_id`/日志 tail、后台 alive/ready（暴露 `GET /health`、`GET /ready`，复用 worker probe 面）。
- 每 `run` 一个 `run_id`，贯穿日志/通知/账本（Run Audit，§54）。
