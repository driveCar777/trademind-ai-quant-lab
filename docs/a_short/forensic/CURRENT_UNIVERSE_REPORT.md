# CURRENT_UNIVERSE_REPORT.md

> A-Short **当前**股票池与 eligibility 真相（只看代码，未改动）。来源：`cn_a_short/baseline.py`、`run_baseline.py`、`cn_a_share_ml_v25/top_n_book.py::board_mask`、合同 `A_SHORT_D1_RESEARCH_CONTRACT.md §2/§6`。

---

## 1. 当前 universe（代码默认）
| 维度 | 现状 | 证据 |
|------|------|------|
| A 股全部？ | **是**（ALL A 普通股） | `run_baseline` `boards="ALL"` → `board_mask` 返回全 True |
| 主板（sh.60/sz.00） | **含** | board_mask ALL |
| 创业板（sz.30） | **含** | ALL |
| 科创板（sh.688） | **含** | ALL |
| 北交所（bj.） | **含** | ALL |
| ST / *ST | **含**（不排除） | `simple_eligible(exclude_st=False)` 默认 |
| 退市风险股 | **含到退市当日**（PIT `listed`），退市后剔除 | `listed==1` 判定 |

## 2. 当前 eligibility（`simple_eligible` 默认）
```python
elig = (listed==1) & (tradestatus==1) & isfinite(close) & (close>0) & (listed_cum >= min_hist)
min_hist   = 20      # 仅 20 交易日 IPO seasoning（≈1 个月）
exclude_st = False   # ST 纳入
MIN_ELIGIBLE = 200   # 当日合格<200 只 → 不出信号
```
成交时（非选股时）另有：停牌 `SUSPENDED`、一字涨跌停 `LIMIT_LOCK`、缺开盘 `MISSING_OPEN`、零量 `ZERO_VOLUME`、退市 `DELISTED`（`exec_reason`）。

## 3. 质量过滤：有 / 无
| 过滤器 | 当前是否有 | 说明 |
|--------|:---:|------|
| 市值下限 | **无** | 无 market-cap 数据接入，无 floor |
| 成交额下限 | **无** | pack 有 `amount` 字段但未用作 filter |
| 换手率下限 | **无** | pack 有 `turn` 但未用作 filter |
| 流动性/ADV | **无** | 无 |
| 股价下限 | **无** | 无 penny 过滤（¥5 最低佣金带未回避） |
| 上市时间 | **弱**（min_hist=20 交易日） | 仅极短 IPO seasoning |
| 财务质量 | **无** | 无财务数据接入 A-Short |
| ST 排除 | **无**（默认 False） | ST 纳入 |
| 停牌过滤 | **有**（成交时） | tradestatus / SUSPENDED |
| 涨跌停过滤 | **有**（成交时） | LIMIT_LOCK（不影响选股排序，只影响成交） |

## 4. 是否天然偏向低质量
```
ALL universe（含 ST/微盘/低价/科创/创业/北交所，20–30% 涨跌幅）
+ 打分 = 20 日动量（近 20 日涨最多）
+ 无 价格/成交额/换手/市值/财务 质量下限
⇒ Top-K 天然富集：
```
| 倾向 | 是否天然偏向 | 机制 |
|------|:---:|------|
| 小盘股 | **是** | 小盘振幅大，20D 动量更易极端 |
| 低价股 | **是** | 低价名义涨跌幅更大；且无价格下限 |
| 高波动股 | **是** | 动量对高波动名字选择性偏好 |
| "垃圾股"（ST/绩差） | **是**（不排除 ST，无财务门） | ST/题材/概念常有脉冲动量 |
| 流动性陷阱 | **是**（无 ADV/成交额门） | 可能选到日成交极低、实际难成交/滑点大的名字 |

## 5. 三层归因（不可混淆）
- **UNIVERSE DESIGN**：合同 §2/§6 明确 = ALL + **故意不含**质量过滤（第一批为纯数值 baseline）。这是**设计**，不是 bug。
- **MODEL BEHAVIOR**：20D 动量对高波动/低价/小盘有内生偏好。
- **DATA QUALITY**：与"垃圾股"现象**无关**（不是坏数据造成）。

## 6. 影响与纪律
- 任何 Top-K 表现**必须先归因于小盘/低价 β**（与 ML1 系列「大半是 β」教训一致），再谈 alpha。
- 无 ADV/成交额门 → 回测的可成交性被高估的风险（`baseline.py` 已建模停牌/涨跌停/carry/STUCK，但**未建模成交量冲击/流动性上限**）。
- **本阶段不加任何过滤器**（禁止）。若要研究过滤器 → 仅登记 `A_SHORT_D1_V2 HYPOTHESIS`（见 `A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md §11`），须新预注册 + 独立证明增量，**不改 V1**。

## 7. 结论
当前 A-Short universe = **全 A 股、含 ST、无任何质量/流动性/市值/价格过滤**，配 20D 动量 ⇒ **结构性偏向低价/小盘/高波动/垃圾股/流动性陷阱**。这是**合同设计特征（BASELINE_DESIGN_CHARACTERISTIC）**，需在解释任何未来结果时显式扣除小盘 β，且提醒可成交性被高估的风险。
