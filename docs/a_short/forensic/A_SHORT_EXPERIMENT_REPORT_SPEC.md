# A_SHORT_EXPERIMENT_REPORT_SPEC.md

> 每次 run 自动生成的 `REPORT.md` 规范。重点：**结果不好时必须解释"为什么不赚钱"，不能只写 FAIL。**

---

## 1. 结构（11 节）
1. **Experiment Identity** — RUN_ID、git commit/branch/dirty、python/OS/deps、model_name/version、seed。
2. **Data** — upstream/derived id+hash、pack_exists、`data_status`(READY/DATA_BLOCKED/DEGENERATE)、coverage/missingness。
3. **Universe** — total/eligible/excluded；board 计数（主板/创业/科创/北交所）+ ST；price/turnover/volatility 分位（防"只是买垃圾小票"）。
4. **Signal** — 每日候选密度、Top-K 分数分布、feature 摘要、eligibility/reject 分布。
5. **Execution** — entry/exit fill 率、`n_entry_limit_lock`/`n_exit_limit_lock`/`n_suspended`/`n_stuck`/`n_no_lot`、`carry_rate`、`forced_hold_days` 分布。
6. **Cost** — fee-only / slippage / net 拆分；turnover（单边/往返/再平衡次数/平均持有）；min-fee 绑定率。
7. **Performance** — benchmark(EW/动量) return、excess、strategy net、hit rate、逐期分布、MaxDD。
8. **Attribution** — Total ≈ Beta + Sector + Size + Momentum + Selection − Cost（基础版见 §2）；best/worst 10 trades。
9. **Failure Analysis** — `ERRORS.json` 摘要 + `primary_conclusion`（STYLE_EXPOSURE_ONLY / TRUE_NO_EDGE / COST_ERROR / …），**明确"不赚钱的原因"**。
10. **Limitations** — 已知简化（overlap 占用未计、STUCK 假设清算、滑点未实测、无 ADV 门、20D 动量非短线、universe 偏小盘 β、Cloud DATA_BLOCKED）。
11. **Reproduction Command** — 精确命令 + normalized manifest hash + `REPRODUCIBILITY=PASS/FAIL`。

## 2. Attribution（基础版，必须实现的最小集）
- `benchmark_return`（EW eligible / 指数）、`excess_return = strategy − benchmark`。
- `topk_contribution`（各 Top-K 桶对总收益的贡献）。
- `best_10_trades` / `worst_10_trades`（symbol/entry/exit/net/status）。
- **Size/Momentum 暴露（近似，标注）**：用 DATA_SNAPSHOT 的价格/波动分位 + momentum 分数近似暴露；**无真实市值/行业数据前，Sector/Size 归因标记 `APPROX`，不得当精确**。
- 结论句式：例如「Total +X%；其中 excess vs EW ≈0（t 不显著）→ 收益主要是小盘 β，Selection alpha ≈0」。

## 3. "为什么不赚钱"话术要求
- 禁止只写 `FAIL` / `NO_ALPHA` 无解释。
- 必须给出**主因 + 证据**，例如：
  - 「COST_ERROR：turnover 100%/期、min-fee 绑定 70%，net≪gross → 成本吞噬」
  - 「STYLE_EXPOSURE_ONLY：excess vs EW t=0.1 → 纯 β，非 selection」
  - 「EXECUTION_ERROR：exit LIMIT_LOCK 使 12% 仓位 STUCK → 回测高估可成交性」
  - 「TRUE_NO_EDGE：gross/excess/net 全不显著且执行/成本/数据正常 → 该信号无短线边」

## 4. 产出与提交
- `REPORT.md` 小、可入 git；逐日 SIGNALS/TRADES 大件 gitignore。
- 报告不得声称 alpha / 收益承诺 / ready for paper（治理红线）。
