# Paper Hot MT5 Desk — Ava demo 分品种台（只 :9001）

**日期：** 2026-09-12  
**端口：** `http://127.0.0.1:9001/paper` 融合视图底部卡片  
**定性：** 执行观察台。**不是 Candidate。** 不改 `:9000` / `daily.py` / ML1。不重开 V1–V8 / V30 / V32。

## 1. 为什么和 A 股数据不打架

A 股本地日线要等主人工作日晚上点 `:9000` 更新。MT5 报价从本机 **Ava Trade 终端**实时读，不走 BaoStock，不读 `live/bars`。两套时钟分开。

## 2. 频率（我定的）

不剥头皮、不 H1 搜参。工作日 **08:30（亚洲）/ 20:30（纽约上午）** 各 1 次 Grok，覆盖全部品种一本 JSON。每品种每场最多 1 笔，手数 0.01。周末跳过。

## 3. 品种账

| id | 品种 | 逻辑提示（给 Grok，不是回测参数） | 发单 |
|---|---|---|---|
| XAUUSD | 黄金 | 实际利率 / 美元 / 避险 / 地缘 | demo |
| CRUDE | 原油 | 供需 / OPEC / 地缘 / 美元 | demo |
| EURUSD | 欧美 | 欧央行-美联储利差 / 风险 | demo |
| USDJPY | 美日 | 利差 / 干预风险 | demo |
| GBPUSD | 美英 | 英央行 / 英国数据 | demo |
| USDCAD | 美加 | 油价 / 加央行 | demo |
| USDCHF | 美瑞 | 避险 / 瑞央行 | demo |
| SHARES | 美股 CFD 篮子 | AVA 股票少；V30 成本死 | **只建议** |

符号按终端别名解析（GOLD / CrudeOIL / XAUUSDm 等）。

## 4. 发单闸门

- `account_mode=live` → 拒绝
- `TRADEMIND_HOT_SMOKE=1` 或 `TRADEMIND_MT5_SEND=0` → 只记账
- 页面「demo 发单」开关（`MT5_SETTINGS.json`，默认开）
- `priced_in=true` 的开仓丢掉

## 5. 读取

这不是预注册边。demo 盈亏不作 Level-1。A 股融合台仍按 §7c 两个月后读一次。
