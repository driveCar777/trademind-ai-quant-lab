# Phase 1 Design — 一键启动状态以健康检查为准

> **模块：** 运维补强（不是 V4）  
> **日期：** 2026-08-23  
> **状态：** Phase 3 Smoke 09 PASS（2026-08-23）。Phase 4/5 本轮不做。

## 1. 要解决什么

现在 `start_all.bat` 用 `netstat | findstr ":9000"` 判断「已经在跑」：

- 会误匹配别的端口字符串
- 端口在听 ≠ 调度中心健康
- `:9100` 被占但模型没加载时，会跳过启动，却仍可能报「已就绪」
- `start_lab.bat` 只报两个退出码，不说六项里谁好谁坏

本轮只把**判断和收尾说明**做准。不新开 API，不重启通义千问，不开始 V4。

## 2. 判断规则

本机地址只来自环境变量，默认 `127.0.0.1`。Xavier 状态只问 Master `GET /workers`，脚本里不写死板子 IP。

| 对象 | 已在跑（跳过启动） | 应启动 | 禁止再开窗口 |
|------|-------------------|--------|--------------|
| 调度中心 | `GET :9000/health` 为 healthy | TCP 连不上 | TCP 通但 health 不是 healthy |
| 通义千问 | `model_loaded`，或 HTTP 200 仍在加载 | TCP 连不上 | TCP 通但不是网关 JSON |
| Xavier | 不在本机用 netstat 猜 | 仍走现有 SSH 脚本 | — |

`--check-master` 退出码：`0` 跳过，`1` 启动，`2` 端口占用且不健康。  
`--check-gateway`：`0` 跳过（已加载或正在加载），`1` 启动，`2` 占用且不是网关。

收尾 `lab_status.py`（默认）：

```
LAB_STATUS
Master     ONLINE
Gateway    ONLINE | LOADING | OFFLINE
worker-01  ONLINE | OFFLINE
...
LAB_STATUS_OK | LAB_STATUS_PARTIAL | LAB_STATUS_FAIL
```

退出码：`0` 六项都好；`1` 调度中心不健康；`2` 调度中心好但有缺。

弹窗用这些行，禁止再写笼统的「已就绪」掩盖离线节点。

## 3. 不做

- 不改 Worker、不改计算接口
- 不新增 Master 路由 / 错误码
- 不网页一键重启全实验室
- 不在冒烟里关进程或再跑一遍会弹窗的 `start_lab.bat`

## 4. 五阶段

| Phase | 本轮 |
|-------|------|
| 1 Design | 本文 + SPEC §15.5 + Decision 021 |
| 2 Implement | `scripts/lab_status.py`；`start_all.bat` / `start_lab.bat` |
| 3 Smoke | `tests/smoke/09_lab_status.py`（只探活，不启动窗口） |
| 4 / 5 | 不做 |
