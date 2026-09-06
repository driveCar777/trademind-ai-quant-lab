# V36 合同 — A 股行业收益 → 国内期货截面（`CN_INDUSTRY_TO_FUTURES_V36`）

> 2026-09-06 11:40，跑前冻结，只算一次。用户要继续推；小资金翻倍 / 为大资金另调一套外壳**不在本合同**（V33 已证伪彩票；V26.8 冻结）。本层与 V31（价格/持仓/期限）和 V35（全市场指数、四品种同 X）都不同：每个期货品种映射到一个**事前写死的行业桶**，特征因品种而异。$0。m+1。

## 0. 跑前修订（分数未生成）

行业 as-of 文件止于 **2024-02-15**（与冻结面板同一截断）。因此划分改为：

- 研究 2019-07-01 → 2022-06-30（冻结模型）
- 验证 2022-07-01 → 2024-02-29
- 滚动：2019-07→2020-12 / 2021 / 2022H1 / 2022-07→2023-06 / 2023-07→2024-02

修订原因是数据终点，不是结果。

## 1. 对象

- 宇宙 / 标签 / 成本 / LS 三分位 = 与 V31 相同（同合约 20 日开盘→开盘，3.3 bp/边，合格规则同 V31）。
- **不用** V31 的 8 个量价/期限特征。

## 2. 行业桶（事前固定，中英文/2015 税制都能匹配）

| 桶 | 行业标签子串 |
|---|---|
| METAL_NF | 有色 |
| METAL_FE | 黑色金属、C31 |
| ENERGY | 石油、煤炭、燃料、天然气 |
| AGRO | 农业、农副、食品、畜牧、渔业、A01、A03、A04、C13、C14 |
| CHEM | 化学原料、化学纤维、橡胶、塑料、C26、C28、C29 |
| TEXTILE | 纺织、C17、C18 |
| FIN | 银行、货币金融、资本市场、保险、金融保险、J66、J67、J68 |
| BUILD | 非金属矿物、C30 |
| PAPER | 造纸、C22 |
| POWER | 电力、D44 |

品种 → 桶（未列出的品种当日特征 NaN，不入截面）：

- METAL_NF：CU AL ZN PB NI SN AU AG AO BC
- METAL_FE：RB HC WR SS I J JM SF SM
- ENERGY：SC FU LU PG ZC BU
- AGRO：A B M Y P OI RM C CS RR JD LH AP CJ PK SR
- CHEM：L V PP TA MA PF BR RU NR PX SH
- TEXTILE：CF CY
- FIN：IF IH IC IM T TF TS TL
- BUILD：FG SA
- PAPER：SP
- POWER：—（无直接品种；桶仍计算，供相对特征用）
- SI LC PS UR EC BB FB → CHEM / BUILD / AGRO 的指定：SI→METAL_NF，LC→CHEM，PS→CHEM，UR→CHEM，EC→FIN，BB→PAPER，FB→PAPER

PIT：当日用 `effective_date ≤ t` 的最近一个月行业归属。桶收益 = 该日子串匹配到的全部行业的成分股等权日收益。

## 3. 特征（5 个，全部来自映射桶）

`IND_RET_20`、`IND_MOM_60_20`、`IND_REL_MKT_20`（桶 20 日 − A 股合格等权 20 日）、`IND_VOL_60`、`IND_REV_5`。截面排名后进模型。

## 4. 模型

LightGBM，V25 参数。目标 = 20 日同合约收益截面排名。训练 2018-06 起、stride 5、embargo 21。首预测 2019-07-01，研究期每 240 日 refit，**2022-06-30 后冻结**。

## 5. 门（同 V31，验证窗较短事先接受）

G1 验证 LS > 0；G2 验证毛价差 t ≥ 3；G3 滚动 ≥ 4/5；G4 研究 LS > 0；G5 验证 LS 与 ML1 V26.8 期收益 |corr| < 0.3（对齐容差 10 日，因两边信号日不同）。

全过 → `CN_INDUSTRY_TO_FUTURES_V36_LEVEL1`；否则 `NO_CANDIDATE`。

## 6. 事前预期

行业是需求侧代理，逻辑清楚，但 V16 行业层在股票上已无边；映射到商品是新测试，期望弱。G2/G3 仍是主敌。

## 7. 禁止

不改映射表；不加 V31 特征；不扩桶；不把验证改回 2026；不为小资金另做翻倍账本。
