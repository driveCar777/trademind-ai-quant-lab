# RESEARCH_MEMORY_DESIGN.md

> Phase 6 — 长期研究记忆设计。目的：跨会话/跨 AI 的**制度记忆**，防止未来重复已做过的实验、重开已否决的方向。**只设计。**

---

## 1. 目录结构
```
research_memory/
├── hypothesis/     HYP_<NNNN>.json      预注册假设（提出即登记，含预期比较数 m）
├── experiments/    EXP_<NNNN>.json      实验登记（绑定 EXPERIMENT_PROTOCOL 字段 + run_ids）
├── accepted/       ACC_<NNNN>.json      被采纳的结论/候选（含证据 + 审计通过记录）
├── rejected/       REJ_<NNNN>.json      被否决的方向（含 do_not_retry + 原因）
├── failures/       FAILURE_ATLAS.json   失败图谱（见 FAILURE_ATLAS_DESIGN）
└── decisions/      DEC_<NNNN>.json      owner/AI 决策记录（时间戳 + 依据 + 链接）
```
- 全部小 json，入 GitHub（无 raw data）。追加式，**只加不改历史**。

## 2. 记录 schema（要点）
- `hypothesis/HYP`: `{id, date_utc, statement, layer(0-4), features[], universe, hold, expected_comparisons_m, prereg_frozen:true}`
- `experiments/EXP`: `{id, hypothesis_id, dataset_hash, code_commit, contract_id, parameter_hash, model_version, run_ids[], status}`
- `accepted/ACC`: `{id, experiment_id, claim, evidence, audits_passed[], corr_vs_ml1, net_after_cost, caveats}`
- `rejected/REJ`: `{id, experiment_id, reason, failure_class, do_not_retry:true, unless:"new data/new contract/new evidence"}`
- `decisions/DEC`: `{id, date_utc, question, decision, rationale, links[]}`

## 3. 使用协议（每个 AI/会话必须遵守）
```
开始研究前:
  1. 读 research_memory/rejected/ + failures/FAILURE_ATLAS.json → 已否决/已死方向不再开
  2. 读 accepted/ → 已确立结论不重证
  3. 读 decisions/ → owner 硬约束（如“不进 V2”、“数据未解冻”）
提出实验:
  4. 写 hypothesis/HYP → experiments/EXP（预注册冻结）
结束实验:
  5. PASS → accepted/ ；FAIL → rejected/ + failures/ ；并写 decisions/
```

## 4. 与现有制度对齐（不重复造轮子）
- 现状：项目的“制度记忆”散落在 `AGENTS.md`（阶段冻结记录）+ `docs/…/FAILURE_ATLAS.json`（ML1）+ 各 `CONTRACT/DECISION.json`。Phase 6 的 `research_memory/` 是 **A-Short 专用、结构化、机器可查**的统一入口，**不改** AGENTS.md/旧 atlas，只新增 A-Short 命名空间。
- 现有 A-Short 决策应回填 `decisions/`：如“20D 动量仅 CONTROL”“不进 A_SHORT_D1_V2 直到有 empirical”“数据 DATA_BLOCKED 需 owner 解冻”“LLM 无交易权”。

## 5. 防重复的硬规则
- 新实验若与 `rejected/` 中某条 `do_not_retry` 等价（同 hypothesis/feature/universe/hold）→ **拒绝**，除非携带 `unless` 条件（新数据/新合同/新证据）。
- Cloud 分析每份 experiment_report 后**必须**写回 `research_memory/`（否则记忆断层）。
- 10 年后复现：由 `experiments/EXP` 的 dataset_hash + code_commit + parameter_hash + manifest_hash 可精确定位“哪份代码/数据/参数”（见 `PHASE6_DECISION_REPORT §5`）。
