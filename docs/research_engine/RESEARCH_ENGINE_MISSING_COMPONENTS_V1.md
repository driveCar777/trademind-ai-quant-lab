# Research Engine Missing Components V1

Program: `ALPHA_PROGRAM_V1`. Phase 5.  
Audit of `research_engine/` on disk. **Do not implement in this task.**

---

## Executive Summary

Level 0 的「发现引擎」是齐的：合同、hash、FDR、bootstrap、OOS 拒访、四 Xavier、单策略成本与仓位。  
缺的是 Level 2–3 的 **书本会计**：组合账本、暴露限额、跨品种同步持仓、融资/隔夜、滑点期限结构。

现在就实现组合引擎 = 负 EV。没有 Level 1 袖套。

---

## 1. 已有（不要重写）

| 组件 | 路径 | 够 Level 1 吗 |
| --- | --- | --- |
| 点差 + 5bp 佣金 + 10bp 滑点 | `profit/cost/model.py` | 是（单笔） |
| NEXT_BAR_OPEN；禁 close | 同上 | 是 |
| 0.5% 风险、1×、1.5×ATR | `profit/risk/sizing.py` | 是（单笔） |
| 同品种三袖套等权 | `profit/portfolio/combine.py` | 否；假组合 |
| 状态水平 | `regime/state.py` | 是；缺 Δstate 模块 |
| 跨品种作业 | `cross_asset/` | V0.8 专用 |
| 统计 | `statistics.py` | 是 |

---

## 2. 缺口（按「离赚钱的距离」）

### 现在缺、但 V0.9 **不需要先做**

| 缺口 | 说明 | 何时做 |
| --- | --- | --- |
| Δstate helper | 从 `state[t]`−`state[t-1]` 出转换，避免实现时写成水平 | V0.9 实现任务里最小做 |
| 路径基准报告器 | 无条件多 GOLD/OIL | V0.9 报告必出 |
| 重叠持仓策略 | 合同已写 skip；代码要执行 | V0.9 实现 |

### 现在缺、且 **不准提前做**（无袖套）

| 缺口 | 说明 |
| --- | --- |
| 跨品种组合会计 | 对齐日历上的多袖套权益、相关、边际 DD |
| 暴露控制 | 净美元、净商品、总杠杆、单标的上限 |
| 组合再平衡规则 | 日频/周频；现在无输入 |
| 策略间相关矩阵 | 要两条以上权益曲线 |

### 真缺、被数据挡住

| 缺口 | 说明 |
| --- | --- |
| 隔夜/掉期成本 | 无利率；Carry 假 |
| 滑点=波动函数 | 只有常数 10bp；可当诊断，不可当新假设 |
| 成交量冲击 | `real_volume=0` |
| 期权希腊 / IV | 无 |

### 工程债（不阻塞发现）

| 缺口 | 说明 |
| --- | --- |
| 无统一 `research_engine/regime_transition/` | V0.9 还没有包 |
| 根目录无 `registry/` | 实验身份散落 JSON |
| Xavier 无 pandas/numpy | 新代码必须 stdlib |
| `catalog.py` 草稿名 | 不得当正式身份 |

---

## 3. 对用户五个问题的直接回答

| 问 | 答 |
| --- | --- |
| transaction cost model | **有**（半价差+5bp+10bp）。缺：掉期、波动滑点 |
| slippage model | **有常数**。无冲击模型 |
| position sizing | **有单笔**。无组合风险预算 |
| portfolio accounting | **仅同品种等权诊断**。无真账本 |
| exposure control | **仅 1× 与 FRICTION skip**。无组合暴露 |

---

## Decision

不在本任务实现任何缺口。  
V0.9 实现时只补 Δstate + 重叠 skip + 基准报告。组合层等 Level 1。

---

## Next Automatic Action

Phase 6：冻结 Level 1 / Level 2 验收门。
