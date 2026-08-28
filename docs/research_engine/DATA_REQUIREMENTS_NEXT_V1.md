# Data Requirements Next V1

Program: `ALPHA_PROGRAM_V1`. Phase 7.  
What to fetch later. **Do not fetch now.** Do not overwrite `*-20260825-000001`.

---

## Do not block V0.9

V0.9 只需现有 GOLD D1 + OIL D1。数据门 **OPEN**。

---

## Next fetches (priority)

| 序 | 需求 | 打开什么 | 方法 | 失败怎么记 |
| ---: | --- | --- | --- | --- |
| 1 | 更长 M15/H1 新 `dataset_id` | 时段主证、诚实短周期年化 | Data Layer V0.2 只读；`parent_dataset_id` 指向 000001 | `history_shortfall` / Max. bars |
| 2 | 更长 D1（若终端有） | 更稳 CAGR | 新 id，不覆盖 | 仍从 2020 起则记「无更早」 |
| 3 | 事件日历（CPI/NFP/EIA） | Event 家族 | 独立只读表 + 时间戳 | 无表则整季跳过 |
| 4 | 短期利率或掉期代理 | Carry | 新表 | 无则 Carry 永 BLOCKED |
| 5 | ATM IV 或期货曲线 | 真 VRP | 新表 | 无则不准用 ATR 冒充 |
| 6 | 非零 `real_volume` 或 DOM | 流动性 | 换源/换品种 | 否则不要再扫 tick_z |

禁止：把新下载的尾巴叫 Final OOS。禁止 `order_send`。

---

## Explicitly not requested this quarter

DXY（可用 FX 代理但禁止写成 DXY）、股票、加密、新闻爬虫、另类卫星。
