# A_SHORT_CLOUD_HANDOFF_FINAL.md

> Cloud→Local 工程交接最终报告。坏消息优先；只记录，不修补，不绕过。

---

## BAD NEWS FIRST
1. **empirical alpha 从未跑过**：冻结 D1 面板字节在 Cloud 不可用（`REGISTERED BUT BYTES UNAVAILABLE`）。
2. **唯一模型 = 20D 动量 baseline**，非最终策略，方向偏中周期；短线特征族 0 实现。
3. **20 项需求：9 项 Missing（无代码）、10 项 Partial（未接/无字节）、仅引擎+算术已实现。**
4. **universe 天然偏垃圾股**（ALL + 无质量过滤，设计特征）——未来任何收益先扣小盘 β。
5. **无 alpha 证明；无 live 运行时**（:9002/GUI/通知/scheduler/账本全文档级）。

---

## STATUS
```
STATUS:      READY_FOR_LOCAL_CONTINUATION
Environment: Cursor Cloud VM
Code:        READY        (33 tests 绿；report_tables 确定性；run_baseline=DATA_BLOCKED)
Data:        EXTERNAL / BLOCKED   (冻结字节不在 git/Cloud；不随交接)
Alpha:       NOT PROVEN
Trading:     NOT AUTHORIZED
Next Step:   LOCAL CONTINUATION   (先做 G0 数据决策)
```

## 交接坐标
```
repo   : github.com/driveCar777/trademind-ai-quant-lab
branch : cursor/a-short-architecture-forensic-3072   (PR #2, 未合并; base main)
commit : 见本次 "docs: freeze cloud to local handoff"
```

## 本地续作最短路径
```bash
git clone <repo> && cd trademind-ai-quant-lab
git checkout cursor/a-short-architecture-forensic-3072
python -m pip install numpy pytest
python -m pytest research_engine/cn_a_short/tests/ -q     # 33 passed
python -m research_engine.cn_a_short.report_tables        # 成本/账户表（无需数据）
python -m research_engine.cn_a_short.run_baseline         # 有冻结 pack 才出 empirical，否则 DATA_BLOCKED
```
可运行：`pytest` / `report_tables`（无需数据）。需数据：`run_baseline` 的 empirical（需本地 D: raw 或先解冻）。

## 交接文档索引
- 环境：`HANDOFF_ENVIRONMENT.md` · `ENVIRONMENT_REPORT.md`
- 状态：`CURRENT_IMPLEMENTATION_STATUS.md` · `CURRENT_MODEL_REALITY.md` · `HANDOFF_CLOUD_TO_LOCAL.md`
- 需求差距：`REQUIREMENT_GAP_MATRIX.md` · `A_SHORT_CLOUD_FINAL_AUDIT.md` · `forensic/*`
- 数据：`DATA_HANDOFF_STATUS.md` · `DATA_STORAGE_POLICY.md` · `A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md`
- 恢复：`LOCAL_RESTORE_GUIDE.md` · `A_SHORT_LOCAL_HANDOFF.md` · `CLOUD_CODE_MAP.md`

## owner 待决策（本地续作前）
1. **数据解冻**：上传冻结字节到 Cloud/本地可达（保 `dataset_id`+`hash`），或授权注册新数据集（新 id/hash + 合同）。不采购、不换源、不改 hash。
2. **信号方向**：是否用短线因子族（新 `A_SHORT_D1_V2`）取代 20D 动量，还是先按 V1 跑完 empirical。

## 下一阶段顺序（复述，详见 A_SHORT_CLOUD_FINAL_AUDIT.md）
```
G0 数据策略 → G1 Universe 设计 → G2 短线因子合同 → G3 baseline → G4 信息层 → G5 LLM 融合 → G6 GUI → G7 Paper Trading
```

## 纪律
本阶段只交接：不开发、不调参、不改 universe/数据源/合同、不加过滤、不接 LLM/新闻/GUI/通知/交易、不跑 alpha、不为收益隐藏缺失。
