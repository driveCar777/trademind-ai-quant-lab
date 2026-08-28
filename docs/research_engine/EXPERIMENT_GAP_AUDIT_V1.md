# Experiment Gap Audit V1

Program: `ALPHA_PROGRAM_V1`. Phase 7.  
Holes in **already-run** experiments. Not an invitation to reopen them.

---

## HYP-0001

- 漏洞：WEAK_SUPPORT 容易被读成「有一点 alpha」。  
- 事实：不是书，不是 10%。  
- 动作：不重跑。知识库已写。

## FD V0.1

- 漏洞：`FAM-FD-XASSET-0001` / NEWS 仍标 DRAFT，看起来像「没做」。  
- 事实：跨品种已由 V0.8 在**不改 FD 文件**的前提下跑完并失败。NEWS 仍无数据。  
- 动作：不要编辑 FD search-space 去「同步状态」（那是改冻结合同）。在地图里写清即可。

## V0.5

- 漏洞：有 `state_id` 却从未差分。看起来像「状态做过了」。  
- 事实：做过水平，没做转换。  
- 动作：V0.9，不是重开 V0.5。

## V0.6

- 漏洞：OIL D1 残留 + M15 垃圾年化会诱人调参。  
- 事实：程序 CANDIDATE=0。  
- 动作：禁止。组合函数是同品种等权，不是真组合。

## V0.8

- 漏洞：同期相关强，诱人做同 bar 或翻号。  
- 事实：滞后成本后全灭。  
- 动作：Decision 043。深度设计已把「同 bar」排除。

## V0.9（未跑）

- 漏洞：还没有 runner；合同已锁。实现时可能把转换写成水平。  
- 动作：测试框架 T7/T8（已写，未编码）。实现任务才许动代码。

## 基础设施

- 无根 `registry/`：身份靠各目录 JSON。可接受，不必为了整齐新建空注册中心。  
- `catalog.py` 草稿名：测试用，调度禁止读它。  
- Final OOS：目录空 + 代码 raise。不要「补数据进去好做完」。

---

## Decision

已有实验的漏洞是 **解读与诱惑**，不是少跑了 RSI。  
不重开。信息增益在 V0.9 执行（另批）或停。
