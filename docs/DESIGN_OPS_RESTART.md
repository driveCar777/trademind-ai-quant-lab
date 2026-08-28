# Phase 1 Design — 控制台运维：启动 / 重启

> **状态：** 已落地 2026-08-22（SPEC §15）。  
> **日期：** 2026-08-22  
> **Stitch：** 炒股项目 `projects/11080649017611725141`  
> **对照：** 落地前必须先改 `SPEC.md`，再改 Master / Dashboard。

---

## 1. 要解决什么

现在启动拆成两个脚本，还要自己开窗口。控制台只能看在线/离线，灰了只能再跑脚本。

目标：

1. **桌面一个图标** = 本机 + Xavier-02/03/04 一次拉起（本轮可做，不新增 API）。
2. **网页上对应按钮** = 某张节点卡启动/重启；顶栏重启调度中心（本轮只设计，落地另开）。

---

## 2. 桌面一键（本轮实现）

| 项 | 说明 |
|----|------|
| 脚本 | `start_lab.bat` = `start_all.bat` + `start_xavier.bat` |
| 快捷方式 | 桌面「TradeMind 一键启动」 |
| 行为 | 9000/9100 已占用则跳过；02/03/04 已健康则跳过；不碰 Xavier-01 |
| 通义千问 | 仍走 `start_sycl.bat`，加载约 1–2 分钟 |

**不做：** 网页里「一键启动全实验室」（那会绕过 SYCL 窗口，容易踩 9100 双开）。

---

## 3. 网页按钮规划（未实现）

### 3.1 谁可以点

| 位置 | 按钮 | 作用 |
|------|------|------|
| 顶栏「调度中心」旁边 | 重启调度中心 | 关掉 :9000 再执行 `start_master.bat` |
| 节点卡（离线） | 启动 | SSH 拉起该板 `server.py`（01 走 Docker，若存在） |
| 节点卡（在线） | 重启 | 先停再拉 |
| 顶栏「通义千问」 | **本版不做** | SYCL 必须 `setvars`，网页进程里起不来 |

一张卡只对应一台 Xavier，不对「随便一个离线节点」混按钮。

### 3.2 接口草案（落地前写入 SPEC）

统一包装：`{success, message, code, data}`。

```
POST /api/v1/ops/worker/{worker_id}/start
POST /api/v1/ops/worker/{worker_id}/restart
POST /api/v1/ops/master/restart
```

`data` 建议字段（未入 SPEC，禁止先写代码）：

| 字段 | 含义 |
|------|------|
| `worker_id` | `worker-01` … `worker-04` |
| `action` | `START` / `RESTART` |
| `accepted` | true 表示已接手，进程可能马上断 |
| `hint` | 给人看的下一句，如「10 秒后刷新」 |

错误：离线 SSH 失败 `TM-1002`；未知 worker 用已有参数错误码，不新造码除非 Decision。

### 3.3 重启调度中心怎么做才不会把页面卡死

不能在当前请求里 `taskkill` 自己再傻等。

1. 接口立刻返回 `accepted=true`。
2. 另拉一个脱离的 `scripts/restart_master.bat`：等 1 秒 → 结束 :9000 → `start_master.bat`。
3. 网页提示「调度中心正在重启，10 秒后自动刷新」。
4. 刷新失败则显示「请用桌面一键启动」。

### 3.4 Xavier 启动 / 重启

复用 `scripts/start_xavier_workers.py` 的探活与 `nohup`，改成按 `worker_id` 单台。

| 节点 | 启动方式 (FACT / 待验) |
|------|------------------------|
| 01 | Docker 映射 8080。**重启命令未在本轮 SSH 核实** → 落地前先 `docker ps` |
| 02 | `/home/dji/factor-worker-v1/server.py` :8080 |
| 03 | `/home/dji/backtest-worker-v1/server.py` :8002 |
| 04 | `/home/dji/monitor-worker/server.py` :8080 |

重启 = 释放该端口 → 再 start。禁止 `killall python`，以免误杀板上别的进程。

### 3.5 边界

- 只服务本机实验室，不是公网运维面板。
- 不做「一键重启全部四台 + 调度 + AI」。
- 不做关机、重装、改密码。
- 网页**不重启通义千问**（必须独立 SYCL 窗口）。
- 不在这一步做 V4「替你选股」。

### 3.6 落地顺序（确认设计后再做）

1. SPEC 写入上述 3 个 POST 与字段。  
2. Master 运维服务（SSH / 脱离重启）。  
3. Dashboard 按 Stitch：卡上双按钮 + 顶栏重启 + 确认框。  
4. 冒烟：启动离线 02、重启 03、重启 Master 后面还能打开 `/dashboard`。

---

## 4. Stitch

项目必须用 **炒股**，不新建项目。桌面稿：四张节点卡带「启动/重启」，顶栏「重启调度中心」，通义千问旁写「请用桌面一键，网页不能重启模型」。

**颜色以设计说明为准，不用项目名自动生成的酒红。** 落地色：底 `#070b12`，卡 `#111827`，边 `#243044`，主按钮蓝，AI 紫，在线绿。
