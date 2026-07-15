---
name: proxy-pool
description: 当用户需要收集、验证、读取代理 IP 池，或向代理池新增信息源时，使用本项目。
---

# Proxy Pool

极简代理池工具：所有 IP 提取源放在 `scripts/sources/`，由 `scripts/fetch_all.py` 统一调度，结果保存到 `proxy_pool.json`。

## 何时使用

- 用户说“收集代理”、“获取 IP”、“验证代理”、“读取本地池”、“新增代理源”等。
- 需要从多个来源聚合 IP:端口。

## 项目结构

```text
proxy_pool_project/
├── scripts/
│   ├── fetch_all.py          # 统一调度
│   └── sources/              # IP 提取源
│       ├── scdn.py
│       ├── proxymist.py
│       ├── zdaye.py
│       └── openclaw.py
├── proxy_pool/               # 验证、存储、读取
├── mcp_server.py
└── skill/SKILL.md
```

## 核心用法

### 收集 IP

```bash
cd proxy_pool_project

# 收集 100 个新 IP
python3 scripts/fetch_all.py --target 100

# 只使用指定源
python3 scripts/fetch_all.py --target 100 --sources scdn,proxymist

# CLI 方式
python3 -m proxy_pool.cli collect --target 100
```

### 验证本地池

```bash
python3 -m proxy_pool.cli verify
```

### 读取本地池

```bash
python3 -m proxy_pool.cli list --json
```

```python
from proxy_pool.storage import load_ips
ips = load_ips("proxy_pool.json")
```

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py` 文件
2. 实现 `fetch(limit=20)`，返回 `ip:port` 列表
3. 在 `scripts/fetch_all.py` 的 `SOURCES` 中注册

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

- `collect_proxies`：收集 IP 到本地池
- `verify_proxies`：验证本地池
- `load_proxies`：读取本地池 IP 列表

## 注意

`scripts/sources/openclaw.py` 仅用于统计/安全研究，不作为代理源。
