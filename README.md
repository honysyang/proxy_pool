# Proxy Pool

自动收集、验证、保存并输出代理 IP 池。池子文件格式为 JSON。

所有 IP 提取源统一放在 `scripts/sources/` 下，由 `scripts/fetch_all.py` 调度，CLI 对外提供统一操作。

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
├── proxy_pool/
│   ├── cli.py                # 对外统一 CLI
│   ├── checker.py            # 验证
│   └── storage.py            # JSON 存储/读取
└── mcp_server.py             # MCP Server
```

## 一键使用

```bash
cd proxy_pool_project

# 默认：收集 100 个 IP -> 验证 -> 保存 -> 输出
python3 -m proxy_pool.cli

# 收集 50 个 IP 到池子（会验证）
python3 -m proxy_pool.cli --target 50

# 只使用指定源
python3 -m proxy_pool.cli --sources scdn,proxymist

# 刷新池子：验证并移除无效 IP
python3 -m proxy_pool.cli --fresh

# 从池子快速输出 10 个 IP（不够则自动收集补足，不验证）
python3 -m proxy_pool.cli --output-count 10

# JSON 格式输出
python3 -m proxy_pool.cli --output-count 10 --json
```

## CLI 参数

| 参数 | 说明 |
|------|------|
| `--target` | 收集 N 个 IP 到池子（默认 100，会验证） |
| `--sources` | 指定源，逗号分隔 |
| `-o, --output` | 池子文件路径（默认 proxy_pool.json） |
| `-p, --protocol` | scdn 协议参数 |
| `--country-code` | scdn 国家代码参数 |
| `-t, --timeout` | 验证超时秒数 |
| `--no-verify` | `--target` 收集后跳过验证 |
| `--fresh` | 验证现有池子，移除无效 IP |
| `--output-count` | 从池子输出 N 个 IP，不够则自动收集补足 |
| `--json` | JSON 数组格式输出 |

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`，实现 `fetch(limit)` 函数
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

## 读取 IP 池

```python
from proxy_pool.storage import load_ips

ips = load_ips("proxy_pool.json")
```

## MCP Server

```bash
python3 mcp_server.py
```

暴露工具：
- `collect_proxies`：收集 IP
- `verify_proxies`：验证本地池
- `load_proxies`：读取本地池

## 关于 openclaw

`scripts/sources/openclaw.py` 仅用于统计/安全研究，不作为代理源。
