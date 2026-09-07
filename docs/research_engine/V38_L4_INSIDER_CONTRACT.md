# V38-L4 合同 — A 股股东 / 高管增减持层（跑前冻结）

> 2026-09-07 00:30 提交。`research_engine/cn_a_share_insider_v38/`。跑完冻结；`DECISION.json` 存在即拒绝再跑。属于 V38 S1。ML1 不动。

## 对象

- 东财 `RPT_SHARE_HOLDER_INCREASE`（股东增减持，含公告日 `NOTICE_DATE`、方向、变动万股、成交均价、占流通比）+ `RPT_EXECUTIVE_HOLD_DETAILS`（高管持股变动，只有 `CHANGE_DATE`）。2007–2024 按年下载 36 表 0 失败：股东 130,812 行、高管 150,888 行。
- **文献事前记录**：A 股高管整体无卖出择时能力（吉大 2022；金融研究 2020 减持新规压缩获利）；实际控制人减持短期正、长期反转；增持可能有信息（朱茶芬 2011）。整层作为一个模型测一次，**不事后拆成只看增持**。

## PIT

股东表：公告日后第一个交易日可见。高管表：`CHANGE_DATE` + 3 个交易日可见（法定 2 个交易日内披露，取保守）。可见日 > 2024-02-29 丢弃。

## 特征（7，120 日回看窗，事前写死）

金额按该股 t 日的 20 日均成交额缩放（流动性相对强度）：INS_NET_AMT、INS_BUY_AMT、INS_NEG_SELL、INS_NET_CNT（增持次数 − 减持次数）、INS_NET_RATIO（股东表占流通比带号累计）、INS_NEG_AGE、INS_LAST_DIR。窗内无事件 = NaN。并列由 `1e-3·tanh(净额)` 打破。

覆盖（有事件的合格股票比例）：2012 年 12% → 2016 年 28% → 2023 年 36%。

## 模型 / 账本 / 门 / 判决

与 V38-L1 完全一致（V25 LightGBM 参数、全宇宙、LO20 闸门、五滚动窗、corr vs ML1 ≤0.90、m=1）。标签：`A_SHARE_INSIDER_TRADES_V38L4_{INDEPENDENT_CANDIDATE|SAME_CLUSTER|NO_CANDIDATE}`。

## 禁止

不搜窗口 / 特征 / 参数；不事后只留增持；不换 HN20；不读禁用窗；不塞进 ML1。
