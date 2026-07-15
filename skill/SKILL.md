---
name: proxy-pool
description: 当用户需要获取代理 IP 池时，使用本项目的 CLI 统一收集、验证、刷新、输出 IP。
---

# Proxy Pool

对外只通过 CLI 提供统一入口，池子文件为 JSON。

三种核心操作：
- `--target N`：收集 N 个 IP 到池子（默认验证）
- `--fresh`：验证并清理现有池子
- `--output-count N`：从池子输出 N 个 IP，不够则自动收集补足

## 何时使用

- 用户说“给我代理池”、“获取 IP”、“爬代理”、“验证代理”、“输出 10 个 IP”等。
- 需要从多个来源聚合 IP:端口。

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

# 收集 100 个并验证
python3 -m proxy_pool.cli

# 收集 50 个
python3 -m proxy_pool.cli --target 50

# 刷新池子（移除无效 IP）
python3 -m proxy_pool.cli --fresh

# 快速输出 10 个 IP（不验证，不够则收集）
python3 -m proxy_pool.cli --output-count 10

# JSON 输出
python3 -m proxy_pool.cli --output-count 10 --json
```

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`，实现 `fetch(limit=20, proxy=None)`
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
- `fresh_proxies`：验证本地池
- `output_proxies`：从本地池输出 N 个 IP（不够则收集补足）
- `load_proxies`：读取本地池

## 注意

`scripts/sources/openclaw.py` 仅用于统计/安全研究，不作为代理源。
