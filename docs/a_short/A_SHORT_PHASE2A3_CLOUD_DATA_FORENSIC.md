# A_SHORT_PHASE2A3_CLOUD_DATA_FORENSIC.md

> Phase 2A.3 — Cloud 数据可用性 + Universe 取证。**Forensic only**：不跑 alpha、不改合同、不改 universe/过滤器、不换数据源、不买数据、不进 Phase 2B。
> 环境更正（硬）：A-Short 研发环境 = **Cursor Cloud VM + GitHub repo**。**不存在**本地 :9000 Master / D: 盘 / AGX / 用户本地库。Phase 2A.2 里「在 :9000 跑」的说法作废。

---

## 1. Environment identity
- 环境：**Cursor Cloud VM**（无本地 Windows Master、无 D: 盘、无 AGX worker、无本地 DB）。
- repo：`driveCar777/trademind-ai-quant-lab`，branch `cursor/a-short-architecture-forensic-3072`，HEAD `4913cce9`。
- 网络：出网可达（BaoStock 域名可连），但见 §7/§8 为何**不能**据此重建冻结数据。

## 2. Git repository state
```
branch: cursor/a-short-architecture-forensic-3072
HEAD:   4913cce9a8db38dec067db8ee52dc4e0def43176
diff --check: clean
LFS:    未使用（无 .gitattributes，git lfs ls-files 空）
tags:   仅 freeze-20260907-paper-ops-v2.1（非数据 release）
```
Git **追踪**的 A 股相关文件 = manifests / quality / catalog / universe-history **JSON**（元数据），以及**其它市场**（FX/futures/alt）的 `immutable/*/bars.csv`。**未追踪**任何 A 股 D1 逐股票 OHLCV。

## 3. DATA_LOCATION_MATRIX
| Location | Exists | Version | Source | Registered? | Usable in Cloud? |
|----------|:------:|---------|--------|:-----------:|:----------------:|
| Git tracked（价格面板） | **NO** | — | — | 仅 manifest/hash | **NO** |
| Git LFS | **NO**（未启用） | — | — | — | NO |
| GitHub Releases | NO（仅 freeze tag，无数据 release） | — | — | — | NO |
| GitHub Actions artifacts | N/A（非持久物化路径） | — | — | — | NO |
| cache（`alpha_cache/`） | **NO**（缺失，且 gitignored L64） | v13_000002 | 派生 | 否 | NO |
| raw/（`raw/daily_panel_v12_1`） | **NO**（缺失，且 gitignored L62） | V12.2 | BaoStock | 否 | NO |
| live/bars | **空**（gitignored L124） | — | live BaoStock | 否 | NO |
| external registered source | BaoStock（`BAOSTOCK_FREE_NO_KEY`） | live | BaoStock | 见 §5 | **重抓≠冻结**（见 §7） |

> 元数据（日历/基础/universe 历史/manifests）**在 git 且齐全**；**缺的正是 18.4M 行的逐股票 OHLCV 字节**。

## 4. Frozen dataset lineage
注册处 = 追踪在 git 的 `data/market/cn_a_share/A_SHARE_PANEL_MANIFEST_V12_2.json`：
```
dataset_id : tm-ashare-EQUITY-D1-20260830-000002
content_hash/raw_hash : dd39193c…ae80   (= A-Short 合同的 upstream_hash)
n_files : 5549      n_rows : 18,418,047
history : 1990-12-19 .. 2026-08-28
license : BAOSTOCK_FREE_NO_KEY   source : BAOSTOCK
disk_d_gb : 123.7   (冻结原始字节曾在原下载机的 D: 盘，约 124 GB)
```
搜索全仓：hash `dd39193c…` **只出现在**「manifest + 各合同 `__init__.py` 常量 + docs」——即**纯注册/文档**。`git rev-list --objects --all` 对 `daily_panel|raw.csv|alpha_cache|tm-ashare-EQUITY` **无命中** → **面板字节从未进入 git 历史**。
→ **`REGISTERED_BUT_BYTES_UNAVAILABLE`**：hash 在 git，实体 18.4M 行/~124GB 不在任何 Cloud 可达位置。

## 5. pack_panel dependency graph
`research_engine/cn_a_share_alpha/pack.py`（首行注释：**"Pack frozen raw CSVs to D: npy. Never call BaoStock."**）：
```
pack_panel():
  读 REFERENCE 日历/BASIC (在 git) ✅
  读 PANEL_RAW/symbols/<symbol>/raw.csv  ← 逐股票冻结原始 CSV（不在 Cloud）❌
  → 写 alpha_cache/*.npy + meta.json
load_pack(): 校验 meta.dataset_id/hash == 冻结值，mmap npy
pack_exists(): alpha_cache/close.npy && meta.json 是否存在
```
**Q1**：pack_panel 是 **`existing local raw → panel`**（只压缩既有冻结 raw 成 npy），**不是** `download → normalize → panel`。它**从不下载**。
**Q2**：raw 不存在时 pack_panel **无 bootstrap/download**、不读环境变量、不自建。另有独立 `cn_a_share/acquire.py`（`BaoSession` → BaoStock 下载）+ `compile_v12_2.py`（编译/冻结）能**重建 raw**，但那是**重新采集**，不是恢复冻结字节（见 §7）。无预置目录、无 env 指向 Cloud 可达副本。
**Q3 根因分类**：`DATA_IGNORED_BY_GIT`（raw/ L62、alpha_cache/ L64）**且** `NOT_IN_GIT_HISTORY`（从未提交）**且** `DATA_REQUIRES_EXTERNAL_SOURCE`（唯一再生源=BaoStock，且不复现 hash）。合成根因 = **`FROZEN_BYTES_UNAVAILABLE_IN_CLOUD`**。不是 `DATA_NOT_CLONED`（本就不在 git）、不是 `DATA_PATH_MISCONFIGURED`（路径对，字节缺）。

## 6. Why Cloud VM lacks frozen bytes
V12.2 完成事实（`CHANGELOG` / `TRADEMIND_CONTEXT` / manifest）：单 downloader 收 5549/5549 → 本地 compile/freeze 到 D:（~124GB）→ **只把 manifest + hash 提交 git**，原始字节 gitignored 留在原机磁盘。Cloud VM 是全新 clone，只拿到 git 内容（元数据），拿不到 gitignored 的本地字节。**这是设计使然（大数据不入 git），不是配置错误。**

## 7. Legitimate recovery paths（审计结论：无）
| 候选恢复路径 | 可用？ | 说明 |
|--------------|:------:|------|
| Git tracked / LFS / Release / Actions artifact | ❌ | 全无（§2/§3） |
| 既有 registered cache / raw | ❌ | 缺失且 gitignored |
| BaoStock 重抓（acquire.py + compile） | ⚠️**不合法作为恢复** | 会得到**新的**、point-in-time 不同的字节；`content_hash` 几乎必然 ≠ `dd39193c…` → **破坏注册 lineage**；`compile_v12_2` 明文「Alpha research 必须引用该 dataset_id+hash，**不要 query live BaoStock**」 |
→ **无任何在不改 frozen lineage 前提下、Cloud 可达的合法恢复路径。** 不发明新源、不换 provider、不改 id/hash（§10/§12 硬约束）。

## 8. Whether re-fetch/materialization is possible
- **恢复注册的冻结数据集**：**不可能**（字节不在任何 Cloud 可达处；BaoStock 重抓≠同一冻结快照）。
- **技术上重新采集一个新数据集**：可行（BaoStock 免费可连），但那是 **NEW dataset**（需新 id/hash + 合同修订），**超出本阶段授权** → 属 owner 决策，不在此执行。
→ 结论：**materialization of `tm-ashare-EQUITY-D1-20260830-000002` = NO。**

## 9. Universe definition（代码真相，未改动）
默认（`cn_a_short/baseline.py` + `run_baseline.py`）：
```
boards            = "ALL"      → 主板 sh.60/sz.00 + 创业板 sz.30 + 科创 sh.688 + 北交所 bj.（全含）
simple_eligible   : listed==1 & tradestatus==1 & isfinite(close)>0 & listed_cum>=min_hist
min_hist          = 20         (仅 20 交易日 IPO seasoning)
exclude_st        = False      (ST/*ST 默认【纳入】)
price requirement = 无
liquidity (amount/turnover/ADV) = 无
market-cap floor  = 无
suspension filter = 有（tradestatus / exec_reason=SUSPENDED，成交时剔除）
limit filter      = 有（exec_reason=LIMIT_LOCK，成交时剔除）
MIN_ELIGIBLE      = 200        (当日<200 只合格则不出信号)
```
**MODEL_USED = 20D_MOMENTUM_BASELINE**（`momentum_scores`，`close(t)/close(t-20)-1`）——目前**唯一实现**的打分；合同其余特征族仅 specified（[RESEARCH_CONTRACT §4](A_SHORT_D1_RESEARCH_CONTRACT.md)）。
> 与合同 §2/§6 一致：universe = ALL A 普通股；第一批为**纯数值 baseline**，**故意不含** price/liquidity/mcap/ST 质量过滤。

## 10. Why low-quality names may appear（机制解释，非修改）
```
ALL universe (含创业/科创/北交所 20–30% 涨跌幅 + ST + 微盘 + 低价)
+ 20D momentum ranking
+ 无 price/liquidity/mcap/ST 质量下限
⇒ Top-K 天然倾向 LOW_PRICE / SMALL_CAP / HIGH_VOLATILITY / ILLIQUID
```
20 日动量选的是「近 20 日涨最多」的名字——**低价/微盘/高波动**天然涨跌幅更大，更容易进 Top-K。必须区分三件事：
- **UNIVERSE DESIGN**：合同设计 = ALL + 无质量过滤（有意，第一批数值 baseline）。
- **MODEL BEHAVIOR**：动量对高波动名字有选择性偏好（机制，非 bug）。
- **DATA QUALITY**：与「垃圾股」现象**无关**（不是坏数据导致）。
**不能**由此断言「垃圾股 ⇒ 有 alpha」，也**不能**断言「垃圾股 ⇒ 数据错误」。这是 **`BASELINE_DESIGN_CHARACTERISTIC`**，会影响后续对结果的解释：任何 Top-K 表现须先归因于「小盘/低价 β」再谈 alpha（与 ML1 系列「大半是 β」教训一致）。

## 11. What must NOT be changed yet
本阶段**禁止**：改 `A_SHORT_D1_V1` 合同/窗口/label/成本；改 universe/boards；加 penny/small-cap/market-cap/quality/ST/liquidity 过滤；换 provider；改 dataset id/hash；跑 alpha/OOS/FDR/Paper；进 Phase 2B。
若认为某过滤器值得研究 → 仅登记为 **`A_SHORT_D1_V2 HYPOTHESIS`**（下方），**不实现**。

### A_SHORT_D1_V2 HYPOTHESIS（仅登记，不实现）
- H-V2-LIQ：加最小成交额/换手/ADV 下限，检验是否降低不可交易 Top-K 比例（须新窗/新预注册/新成本）。
- H-V2-PX：加最低价下限（避开 ¥5 最低佣金主导带），检验净期望。
- H-V2-ST：`exclude_st=True`，检验对 Top-K 稳定性影响。
- H-V2-CAP：市值下限/分层，分离小盘 β。
> 以上均为**未来 V2 假设**，须独立预注册 + 独立证明增量，**不在 2A.3 实现，不改 V1**。

## 12. Final decision
```
DECISION: DATA_BLOCKED
REASON:   FROZEN_BYTES_UNAVAILABLE_IN_CLOUD
exact missing dependency : tm-ashare-EQUITY-D1-20260830-000002 raw bytes
                           (5549 files / 18,418,047 rows / ~124 GB; content_hash dd39193c…ae80)
exact expected path      : data/market/cn_a_share/raw/daily_panel_v12_1/symbols/<symbol>/raw.csv
                           → packed to data/market/cn_a_share/alpha_cache/v13_000002/*.npy
legitimate recovery path : NONE reachable from Cloud without breaking lineage
                           (not in git / not LFS / not release / gitignored; BaoStock refetch ≠ frozen hash)
```
**解除阻塞需 owner 决策（REQUIRES_OWNER_DECISION）**，二选一：
1. 把冻结原始字节上传到 Cloud 可达位置（release/LFS/对象存储），保持 `dataset_id`+`hash` 不变 → 之后 `pack_panel()` 可 `READY_TO_MATERIALIZE`；或
2. 授权用 BaoStock 重新采集并**注册一个新数据集**（新 id/hash + A-Short 合同修订）——这是**新合同**，不是恢复 V1。
在 owner 决策前：**保持 DATA_BLOCKED，不换源、不改合同、不改 universe。**
