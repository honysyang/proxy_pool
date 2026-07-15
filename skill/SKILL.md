---
name: proxy-pool
description: 当用户需要获取代理 IP 池时，使用本项目的 CLI 一键收集、验证、保存并输出 IP。
---

# Proxy Pool

对外只通过 CLI 提供统一入口，自动完成：收集 → 验证 → 保存 → 输出 IP 池。

## 何时使用

- 用户说“给我代理池”、“获取 IP”、“爬代理”、“验证代理”等。
- 需要从多个来源聚合 IP:端口并返回可用列表。

## 项目结构

```text
proxy_pool_project/
├── scripts/
│   ├── fetch_all.py          # 统一调度
│   └── sources/              # IP 提取源
├── proxy_pool/
│   └── cli.py                # 对外统一 CLI
└── mcp_server.py
```

## 核心用法

```bash
cd proxy_pool_project

# 一键获取 100 个代理 IP（收集、验证、保存、输出）
python3 -m proxy_pool.cli

# 获取 50 个
python3 -m proxy_pool.cli --target 50

# 指定源
python3 -m proxy_pool.cli --sources scdn,proxymist

# JSON 输出
python3 -m proxy_pool.cli --json

# 重新生成池子（清空旧数据）
python3 -m proxy_pool.cli --fresh

# 快速分配 10 个 IP（不验证）
python3 -m proxy_pool.cli --output-count 10
```

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`，实现 `fetch(limit)`
2. 在 `scripts/fetch_all.py` 的 `SOURCES` 中注册

示例：

```python
# scripts/sources/my_source.py
import requests

URL = "https://example.com/proxies"


def fetch(limit=20):
    resp = requests.get(URL, timeout=15)
    return ["1.2.3.4:8080", "5.6.7.8:3128"]
```

## MCP 工具

- `collect_proxies`：收集 IP
- `verify_proxies`：验证本地池
- `load_proxies`：读取本地池

## 注意

`scripts/sources/openclaw.py` 仅用于统计/安全研究，不作为代理源。
