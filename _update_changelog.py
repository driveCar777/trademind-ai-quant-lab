#!/usr/bin/env python3
"""Add V2.1 entry to CHANGELOG.md"""
import os

BASE = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK"
cl_path = os.path.join(BASE, "CHANGELOG.md")

with open(cl_path, "r", encoding="utf-8") as f:
    cl = f.read()

v21_entry = """## 2026-07-31 — V2.1 Backtest Worker 增强

### 新增功能

- 4 个新策略: TURTLE (海龟/ATR止损), GRID (网格交易), BOLLINGER (布林带), VWAP (量价)
- 滑点模型: slippage_bps 参数, 买入向上滑/卖出向下滑
- 手续费模型: commission_bps 参数, 双向扣除
- 高级指标: Sharpe/Sortino/Calmar 比率, 盈亏比
- 资金曲线: 50 点采样, 前端可直接画图
- initial_capital 参数, 默认 10000
- ThreadingMixIn 并发安全

### 修复

- Python 3.6 兼容: stdout=PIPE + decode()
- ThreadingMixIn 防死锁
- try/except 保护

### 部署

- Xavier-03 (192.168.1.203:8080) stdlib 部署
- 7 策略全部冒烟测试通过
- 70/70 cross-symbol 组合测试通过

### 已知问题

- Master 探测线程受 Indicator Worker 2s 超时阻塞

"""

lines = cl.split("\n")
insert_idx = 0
for i, line in enumerate(lines):
    if line.startswith("## ") and i > 3:
        insert_idx = i
        break
lines.insert(insert_idx, v21_entry)
cl = "\n".join(lines)

with open(cl_path, "w", encoding="utf-8") as f:
    f.write(cl)
print("CHANGELOG.md updated:", len(cl), "chars")
