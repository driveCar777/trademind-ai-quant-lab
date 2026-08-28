# Stability tests

Phase 4 稳定性。冒烟 PASS 之后才跑。

| 文件 | 模块 |
|------|------|
| `01_research.py` | V4.0 研究一笔：连续 10 次、不双开模型、离线/503 |
| `02_research_chain.py` | V4.1 两步：第一步离线不跑第二步 |
| `03_paper_order.py` | V5.0 模拟单：无确认/锁/非指标拒绝 |
| `04_paper_desk.py` | V6.0 台账：20 次 preview 不落盘 |
| `07_mt5_demo.py` | V9.0 假终端：live 拒绝 / SEND=0 不发 |
