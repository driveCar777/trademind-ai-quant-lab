# ml7_live — ML7 信息层堆叠影子（V38-S3，只输出）

合同：`docs/research_engine/V38_S3_INFO_STACK_CONTRACT.md`。用户 2026-09-07 09:44 授权接入。

- **输入**：`ml1_live/daily.py` 刚用过的 live pack / 合格矩阵（同一批会话）。
- **信息层**：V27 季报 10 + V38 预告 9 + 增减持 7 + 质押 6 = 32 个特征，**不含价格特征**。四个层包通过环境变量重定向到 `live/info_layers/<layer>/{raw,normalized,features}`，冻结研究目录不写。
- **增量**：冻结原始文件硬链接到 live raw 一次；覆盖"未关账"周期（≤400 天）的文件超过 3 天就删掉重抓；再由各层自带的可断点 `download.main()` 补齐到当年。
- **模型**：V25 同参数 LightGBM，REFIT_240 时间表与 ML1 相同（最近 refit 2025-11-06），训练 = 该日之前全部历史（合同：历史窗只作训练）。缓存 `live/models_ml7/`。
- **输出**：`live/signals/SIGNAL_ML7_{date}.json`（前 20%，¥5M 参考等权）、`live/ledger/LEDGER_ML7.json|csv`（与 ML1 同一信号链，`name_overlap_with_ml1` 记与 ML1 前 20% 的重合度）、`live/STATUS_ML7.json`。
- **不做**：不进 SHORTLIST；不发单；`daily.py --no-ml7` 可关；任何异常只记录到 `STATUS.json["ml7"]`，不影响 ML1 输出。
- **读取规则**：≥24 个已结算期后读一次（超额 vs EW t ≥ 2、LO20 > 0、corr vs ML1 < 0.9）。之前的账本数字只是倒计时，不是结论。

独立运行：`python -m research_engine.ml7_live.daily [--asof YYYY-MM-DD] [--skip-fetch] [--force-score]`（用 ML1 已落盘的 live pack，不重新抓行情）。
