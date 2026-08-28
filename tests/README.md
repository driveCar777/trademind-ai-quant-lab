# TradeMind — 集成测试

跨模块集成测试，放在根目录 `tests/`。

## 结构

```
tests/
├── README.md
├── test_master_worker.py    # Master ↔ Worker 联调（V1.2）
└── conftest.py              # 共享 fixtures
```

## 规则

- 各模块单元测试放在模块内 `tests/`（如 `workers/indicator-worker/tests/`）
- 跨模块集成测试放在此处
