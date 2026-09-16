# A_SHORT_LOCAL_HANDOFF.md

> 本地恢复包（一页速查）。把 Cloud 成果安全接到本地继续。

---

## 当前 commit
```
HEAD:   9b85f065c19a859bdccfa09f9745e9861bd788ac
（本次 handoff freeze commit 追加在其后；以 PR #2 分支最新为准）
```

## branch
```
cursor/a-short-architecture-forensic-3072   (PR #2, 未合并)
base: main
```

## 关键文件
- 代码：`research_engine/cn_a_short/{__init__,cost,account,feasibility,baseline,report_tables,run_baseline}.py` + `tests/`
- 合同：`docs/a_short/A_SHORT_D1_RESEARCH_CONTRACT.md`（`A_SHORT_D1_V1`，勿改）
- 设计基线：`docs/a_short/`（Phase 1 / 1.1 / 2A / 2A.1 / 2A.2 / 2A.3 + `forensic/`）
- 交接：`ENVIRONMENT_REPORT.md` · `HANDOFF_CLOUD_TO_LOCAL.md` · `CLOUD_CODE_MAP.md` · `LOCAL_RESTORE_GUIDE.md` · `DATA_STORAGE_POLICY.md` · `A_SHORT_CLOUD_FINAL_AUDIT.md`
- 小 artifact：`data/market/research_engine/cn_a_short/PHASE2A_TABLES.json`（成本/账户，确定性）

## 运行命令
```bash
python -m pip install numpy pytest
python -m pytest research_engine/cn_a_short/tests/ -q          # 33 passed
python -m research_engine.cn_a_short.report_tables            # 成本/账户表
python -m research_engine.cn_a_short.run_baseline             # 有冻结 pack 才出 empirical，否则 DATA_BLOCKED
```

## 已知问题 / 限制
1. **empirical alpha 未跑**：Cloud 无冻结 D1 面板字节（`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`）。本地需有 `raw/daily_panel_v12_1`（~124GB）或先解冻。
2. **唯一打分 = 20D 动量 baseline**，非最终策略，**未证明 alpha**。
3. **universe 天然偏垃圾股**（ALL + 无质量过滤，设计特征）；任何未来收益先扣小盘 β。
4. **未实现**：龙头/热点/板块/涨停/龙虎榜/资金流/新闻/政策/LLM/GUI/通知/自动交易。
5. **forced-hold 重叠会计**是已知简化（carry 频繁时 chained net 会低估占用）。
6. `PHASE2A2_*.json` 带时间戳，会随运行变化——非结果差异，勿反复提交。

## 硬约束（本地继续时遵守）
不改 `A_SHORT_D1_V1`/冻结合同/ML1/V33/hash/execution；不换源；不采购；不接 LLM 救场；不宣称 alpha；不为收益目标改规则。
