# A_SHORT_CLOUD_FINAL_AUDIT.md

> Cloud 阶段最终审计（交接前定稿）。BAD NEWS 已在 `forensic/README.md`；此处给需求差距 + 下一阶段顺序。

---

## 1. 距最初需求还有多少？（逐项 Implemented / Partial / Missing）
| 需求 | 状态 | 说明 |
|------|------|------|
| **短线（超短）** | **Partial（弱）** | 引擎支持 T+1..T+5 持有；但唯一打分是 **20D 动量**（中周期），非短线信号；无分钟数据 |
| **T+1~T+5** | **Implemented（执行层）** | `baseline` 前向标签 + T+1 撮合 + carry/STUCK 已实现并测试；但只对 20D 动量打分回测 |
| **龙头识别** | **Missing** | 无代码 |
| **热点发现** | **Missing** | 无代码 |
| **政策** | **Missing** | 无政策文本/NLP；仓库级 DATA_BLOCKED |
| **基本面** | **Partial（未接）** | 财务/行业等信息层有下载+编译包，但**未接 A-Short** 且 Cloud 无字节 |
| **技术面** | **Partial（极弱）** | 仅 20D 动量；`indicator-worker`（RSI 等）存在但不进 A-Short；其余技术指标未成特征 |
| **AI 辅助** | **Missing（未接）** | `paper_fusion`+`cursor_cloud`（Grok）成熟但**未接 A-Short**；A-Short 无 LLM |
| 板块轮动 / 涨停 / 龙虎榜 / 资金流 | **Missing** | 龙虎榜/资金流零代码；涨停仅 V33 派生（独立冻结，不属 A-Short） |
| GUI / 通知 / 纸面账户 / 自动交易 | **Missing（文档级）** | 无 :9002/PySide6/OS toast/live 账本；无 order_send（且禁止） |

**结论**：真正 Implemented 的只有「离线短周期**引擎** + 20D 动量占位」。相对完整目标（短线热点交易系统 + AI 研究平台），**完成度低**，且被数据不可用硬阻塞。**未证明任何 alpha。**

## 2. 下一阶段正确顺序
```
G0 数据策略        ← 当前卡点（owner 决策：上传冻结字节保 id+hash，或授权注册新数据集）
   ↓
G1 Universe 设计   ← 在数据到位后，用数据诊断小盘/低价 β；决定是否加质量/流动性口径（新合同，不改 V1）
   ↓
G2 短线因子合同    ← 新 A_SHORT_D1_V2：短反转/隔夜跳空/量能/换手/波动/breadth/涨停计数，逐族预注册
   ↓
G3 baseline        ← 跑 20 主比较 + FDR；诚实判 NO_ALPHA/WEAK/INCONCLUSIVE；读 carry/stuck/coverage
   ↓
G4 信息层          ← 仅在 G3 出现成本后可交易边时：接 margin/holders/financial/industry/index/preann（需 bytes）
   ↓
G5 LLM 融合        ← 信息智能+决策支持，无交易权；新闻/政策回测须先建 timestamped PIT 语料
   ↓
G6 GUI             ← PySide6 桌面（Decision A-002），只读控制台，关闭不停后台
   ↓
G7 Paper Trading   ← :9002 后端（复制 paper_ops 骨架）+ 后台通知（Decision A-004）+ 模拟账本；仅在有可交易名单后
```
- **顺序不可跳级**：没有 G0（数据）就没有 G3（baseline），没有 G3 的可交易边就不接 G4/G5，没有可交易名单就不做 G6/G7。
- **Phase 2B（新闻/政策/LLM）= G5**，在 G0–G4 之外，**现在不启动**。

## 3. 交接判定
```
Code:     READY（可测、可出成本/账户报表；33 tests 绿）
Data:     EXTERNAL / NOT INCLUDED（冻结字节不在 git/Cloud）
Alpha:    NOT PROVEN
Trading:  NOT AUTHORIZED
Next:     本地继续（先做 G0 数据决策）
```

## 4. owner 待决策（复述）
1. **数据解冻**：方案 A/B/C/D（见 `DATA_STORAGE_POLICY.md`），保 `dataset_id`+`hash`，不采购、不换源。
2. **信号方向**：是否用短线因子族（G2, `A_SHORT_D1_V2`）取代 20D 动量，还是先按 V1 跑完 empirical。

## 5. 纪律
本阶段只交接、不开发、不优化策略、不为收益目标改规则。所有推进等本地环境 + 数据决策到位后再谈。
