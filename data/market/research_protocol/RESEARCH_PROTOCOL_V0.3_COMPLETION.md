# RESEARCH_PROTOCOL_V0.3 完成报告

日期：2026-08-25。  
实验：`tm-exp-20260825-135208-001`（协议自检，非策略）。  
索引：`RESEARCH_PROTOCOL_INDEX.json`。

## 二十六问

1. Dataset Contract 是否完成？**是。** 16 份在 `contracts/`。hash mismatch → `EXPERIMENT_BLOCKED`。
2. Experiment Contract 是否完成？**是。** write-once；状态机禁止 COMPLETED 后改合同。
3. Window Contract 是否完成？**是。** 16 份 CANDIDATE，UTC 时间戳，不是“第 N 根”。
4. Execution Contract 是否完成？**是。** `NEXT_BAR_OPEN` / `NEXT_BAR_CLOSE`；本阶段验证用 NEXT_BAR_OPEN。
5. Lookback Contract 是否完成？**是。** 默认 120；第一信号 = research_start + lookback。
6. Purge/Embargo 是否完成？**是。** 机制已实现（purge=50，embargo=1）；不是永久唯一数值。
7. Causal Feature Registry 是否完成？**是。** `REGISTRY` + `registry_hash`。
8. 哪些 feature 已实现？SMA、EMA、RSI、ATR、MACD、BOLLINGER、VWAP。
9. Feature golden tests 是否通过？**是。** `tests/research_protocol` 14 tests PASS。
10. Feature purity tests 是否通过？**是。** 四台真实数据 + synthetic，`LEAKAGE_DETECTED=false`。
11. Leakage Sentinel 是否通过？**是。** 未来 index → `FUTURE_DATA_ACCESS`；四台 `sentinel_ok=true`。
12. Synthetic leakage corpus 是否全部检出？**机制通过。** 未来 close/volume/high/low/timestamp 攻击未改变过去 feature（干净实现应不变）。Sentinel 单独检出未来 index。
13. 16 个 dataset 是否全部生成 Candidate Window？**是。** 跳过 GOLD M15 `000002`（非规范副本）。
14. 是否锁定 Final OOS？**否。** `FINAL_OOS_LOCKED=false`。
15. 是否有任何实验结果进入 OOS 选择逻辑？**否。** 窗口只来自 70/15/15 协议。
16. 四台 Xavier 是否全部实际参与？**是。** 01–04 各 6 dataset × 10 次，exit 0。
17. 四节点 deterministic 是否 PASS？**是。** 24/24 行 DETERMINISTIC；4 组交叉 PASS。
18. 是否存在任何 computation mismatch？**否。**
19. 是否存在任何 leakage？**否。**
20. 是否修改 V11.7？**否。**
21. 是否修改 Xavier Worker？**否。** 只用 one-shot probe。
22. 是否修改 Master？**否。**
23. 是否访问 MT5 交易接口？**否。**
24. 是否调用 order_send？**否。** `research_protocol/` 无该符号。
25. 是否启动回测？**否。** 未启动 mine / watchdog / V11.7。
26. 下一阶段最小任务是什么？**Hypothesis Registry：** 为新假设写第一份正式 Experiment Contract。不重跑 GOLD M15 RSI，不锁 Final OOS。

## 强制确认

RESEARCH_PROTOCOL_V0.3 已完成。  
V11.7 主链路未修改。  
Data Layer V0.1 冻结数据未被修改（16+1 份 bars.csv 与 manifest sha256 仍一致）。  
本次没有重新运行 V11.7。  
本次没有修改策略参数。  
本次没有向 MT5 发单。  
本次没有调用 order_send。  
本次没有启动 mine_longrun。  
四台 AGX Xavier 均实际参与了研究协议验证。  
Leakage Sentinel 已通过。  
Feature Purity Test 已通过。  
Cross-node Determinism 已通过。  
FINAL_OOS 仍未锁定。
