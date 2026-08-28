# HUMAN DATA PURCHASE ACTION PACK

Mission: Data Expansion V3.0  
Date checked: **2026-08-28**  
Level: **0**  
Candidate: **0**  
Money spent this mission: **$0**  
Stop reason: **HUMAN_REQUIRED / CREDENTIAL_REQUIRED**

This is the only pack you need to act on. Do not buy a stack.

---

## 购买项目（只买这一项）

**Databento historical CME GC + CL contract panel** using the **$125 new-user credits**.

| 项 | 内容 |
| --- | --- |
| 用途 | 打开真正的商品期货曲线：front/next、expiry、settlement、volume、OI、roll yield、basis。Ava 的 GOLD/OIL 是 CFD，做不到。这不是 CARRY_V1A 隔夜利率的重包装。 |
| 供应商 | Databento |
| 当前价格 | 新用户 **$125 credits**（6 个月过期，每团队一次）。用量按 $/GB。CME Standard **$199/月**（2026-06-22 起；博客 2026-05-29）。**先不要开 Standard。** |
| 历史深度 | 厂商页写 CME **16+ years** |
| 覆盖 | COMEX GC、NYMEX CL，全部合约；需要的话同一账户以后可加 options-on-futures |
| API | 有。注册后发 key。`metadata.get_cost` 可先估价 |
| 授权 | 注册时点选 Databento + 交易所条款。历史研究通常是内部使用。禁止再分发原始行情。 |
| 为什么选择它 | Expected Alpha Novelty 最高、现金最低、可哈希、可重复。Information Gap `GAP-FUTURES-CURVE` 是当前最大空洞。 |
| 为什么不选择其他 | ORATS $599 是 ETF 期权面，不是曲线。CME DataMine 要登录且 $105–$2100/月。FirstRate 要先看购物车价，时间戳/OI 弱于 Databento。Trading Economics 是宏观，且官方价页这边 403，共识/初值未验证。不要再买 GVZ/COT/EIA/UST。 |

---

## 买完以后怎么接

1. 打开本仓库 `.env`（从 `.env.example` 复制）。
2. 写入一行，不要加引号空格花招：

```text
TRADEMIND_DATABENTO_API_KEY=你的key
```

3. 不要把 key 发给聊天、不要截图进 Git、不要写进 JSON。
4. 在 Cursor 说：**「Databento key 已进 .env，继续 V3 acquire。」**
5. Cursor 自动：

```text
fetch → normalize(futures_contract) → knowledge timestamp → validate
→ sha256 → 新 dataset_id → READY_FOR_RESEARCH
→ ALPHA_UNLOCK_MAP_DATABENTO_CURVE
→ 一个新 family，最多 3 假设
→ leakage / deterministic / lineage / FDR 门
→ 四 Xavier（01–03 PRIMARY，04 CROSS CHECK）
→ Candidate 或 KILL 后转 ORATS / 下一源
```

6. 原始大文件留在 Data Layer。Git 只收 manifest / schema / hash / 研究报告。

---

## 研究预算停止规则

购买后：

- 最多 **3** 个独立 family
- 全部 `NO_CANDIDATE` → **重新评估 ROI，不要自动续费 $199/月**
- 禁止用 z_cut / hold / 翻号抢救
- 数据 ≠ alpha。允许贵数据也是 NO_EDGE

---

## 最小组合比较（已选 A）

| 方案 | 内容 | 预算 | 打开的新空间 | 现在买？ |
| --- | --- | --- | --- | --- |
| A | 仅 Databento credits | ≤ $125 credits | 曲线 / roll / basis | **是** |
| B | 仅 ORATS hist | $599 | GLD/USO smile/skew/VRP | 否 |
| C | 曲线 + 期权面 | credits + $599 | 两个机制 | 否，先跑完一个 |
| D | 仅宏观共识 | ~$149+/月 | surprise（若初值存在） | 否 |

---

## Cursor 现在停在哪

```text
DATA_SOURCE_SCAN → VENDOR_RESEARCH → PURCHASE_PRIORITY → WAIT_HUMAN
```

SUPPLY_V1（EIA 产量/开工率）已跑完并杀死。没有 Level 1。没有策略。没有 MT5。
