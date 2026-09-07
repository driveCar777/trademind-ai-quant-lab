# V27 — A 股财务层加深（季报 / 资产负债表 / 现金流）合同

> 预注册。写在第一次运行之前。跑完冻结；不许改特征、参数、hold、成本、账本。
> 机器合同：`data/market/research_engine/cn_a_share_findeep_v27/CONTRACT.json`（含 `contract_hash` 与 `findeep_content_hash`）。

## 1. 为什么这一刀（不是因子农场）

V16 只用了年报 4 个比率（ROE、净利增速、毛利、净利率），V25 只从中取了 2 个。季报层此前从未进入任何合同：
每股盈余意外（PEAD）、单季营收增速、应计质量（Sloan）、现金生成、毛利趋势、资产增速（Cooper）、杠杆变化、以及价格标定的估值 EP/BP。
这些是文献里最老、最被反复验证的会计异象，机制事前写清，符号事前定死。它是**一个信息层 = 一个模型**（修正 A3），不是逐个因子扫。

## 2. 数据（免费，$0）

| 表 | 来源 | 用途 | NOTICE_DATE 审计 |
|---|---|---|---|
| `RPT_LICO_FN_CPD` 业绩报表 | 东方财富数据中心（镜像交易所公告） | 净利、营收、EPS、BPS、每股经营现金流、毛利率、加权 ROE | 原始公告日（2010Q3 → 2010-10）。同一期存在"原始 + 次年可比"两版；**取最早公告的一版** |
| `RPT_DMSK_FN_BALANCE` | 同上 | 总资产、资产负债率 | Q1–Q3 原始公告日；**Q4 只有次年可比版（晚 ~15 个月）**，按知识时间处理后自然作废 |
| `RPT_DMSK_FN_INCOME` / `RPT_DMSK_FN_CASHFLOW` | 同上 | **不用** | NOTICE_DATE 是次年可比公告（晚 12 个月）。已下载留档，不进特征 |

- 报告期 2008-03-31 → 2023-12-31（64 期 × 4 表 = 256 个文件）。
- **PIT 规则**：公告日 N 之后的第一个交易日起可见，直到下一份（按公告顺序）公告为止；晚到的旧报告期忽略。
- **知识时间**：计算某份公告的特征时，只能使用公告日 ≤ N 的其他报告（TTM、YoY 用到的历史值同样受此约束）。
- 公告日 > 2024-02-29 的记录在编译时丢弃（禁用窗不碰）。
- 复述 V16/V25 同一告诫：数值可能是最新重述值配原始公告日（供应商共性）。

## 3. 特征（10 个，固定）

| 名 | 定义 | 事前多头符号 | 文献 |
|---|---|---|---|
| `SUE_Q` | 单季净利 − 去年同季净利，除以过去 8 个同类差分的标准差（≥4 个） | + | Ball & Brown 1968 |
| `REV_YOY_Q` | 单季营收 yoy | + | — |
| `NEG_ACCRUALS` | −(EPS_ttm − 每股经营现金流_ttm)/BPS | + | Sloan 1996 |
| `CFO_TTM_BP` | 每股经营现金流_ttm / BPS | + | — |
| `ROE_TTM` | EPS_ttm / BPS | + | Novy-Marx 2013 |
| `GM_CHG` | 毛利率 − 去年同期毛利率 | + | — |
| `NEG_ASSET_GROWTH` | −(总资产/去年同期 − 1) | + | Cooper et al 2008 |
| `NEG_LEV_CHG` | −(资产负债率 − 去年同期) | + | — |
| `EP_TTM` | EPS_ttm / 当日收盘 | + | Fama-French |
| `BP` | BPS / 当日收盘 | + | Fama-French |

单季值由累计值差分得到；TTM = 本期累计 + 去年 Q4 累计 − 去年同期累计。

## 4. 假设（m = 2，FDR q = 0.05）

| id | 特征 | 问什么 |
|---|---|---|
| `ML2F_LGBM_FINDEEP_ONLY` | 仅上表 10 个 | 季报层**自己**有没有边；若 Level-1 且超额序列与 ML1、H11 相关 ≤ 0.90 → **第二条独立袖子** |
| `ML2_LGBM_FULL_STACK` | V25 的 14 个 + 10 个 = 24 | 季报层加在 ML1 上有没有增量。**事前声明**：它含 ML1 的输入，预期落在 ML1 同簇；SAME_CLUSTER **不替换** ML1（换掉 = 在验证期上选择） |

模型、标签、walk-forward、refit 节奏、embargo、2021-08-24 后冻结：与 V25 完全相同，不调。

## 5. 账本与闸门

- **闸门账本 = LO20**（修正 A1 事前登记；V26 已认定 LO20 是策略账本，HN20 是大小盘价差载体）。HN20 只报告。
- Level-1 = 固定划分闸门（预测净收益 R/V 为正、超额/IC 证据 ≥2、FDR 发现、LO20 资金 R/V 为正）且滚动 5 窗 ≥ 4 正。
- 独立性 = 修正 A4：超额-vs-EW MEAN_FORWARD 序列与 ML1（`V25/SCORES_ML1_LGBM.npy` 冻结分数）和 H11 的相关 > 0.90 即 SAME_CLUSTER。
- 成本模型 `A_SHARE_STRATEGY_COST_MODEL_V1` 不变。Final OOS DENIED。不 Paper。不采购。不改 ML1。

## 6. 结局表（事前）

| 结果 | 标签 | 下一步 |
|---|---|---|
| ML2F Level-1 且独立 | `NEW_INDEPENDENT_CANDIDATE`, NEW_INDEPENDENT=2 | STOP A → 复现电池（照 V25.1）→ 两袖组合合同 |
| 仅 ML2 Level-1 且同簇 | `LEVEL1_SAME_CLUSTER_AS_ML1` | ML1 不变；记录季报层增量为诊断；不换模型 |
| 都不过 | `A_SHARE_FINANCIAL_DEEP_MODEL_V1_NO_CANDIDATE` | 冻结；进 FAILURE_ATLAS；不移窗、不改符号 |
