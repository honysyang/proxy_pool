# Proxy Pool

自动收集、验证、保存并输出代理 IP 池。

所有 IP 提取源统一放在 `scripts/sources/` 下，由 `scripts/fetch_all.py` 调度，CLI 对外提供一键化操作。

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
│   └── storage.py            # 存储/读取
└── mcp_server.py             # MCP Server
```

## 一键使用

```bash
cd proxy_pool_project

# 默认：收集 100 个 IP -> 验证 -> 保存 -> 输出
python3 -m proxy_pool.cli

# 收集 50 个 IP
python3 -m proxy_pool.cli --target 50

# 只使用指定源
python3 -m proxy_pool.cli --sources scdn,proxymist

# JSON 格式输出
python3 -m proxy_pool.cli --json

# 跳过验证
python3 -m proxy_pool.cli --no-verify
```

## CLI 参数

| 参数 | 说明 |
|------|------|
| `--target` | 目标收集数量（默认 100） |
| `--sources` | 指定源，逗号分隔 |
| `-o, --output` | 输出文件（默认 proxy_pool.json） |
| `-p, --protocol` | scdn 协议参数 |
| `--country-code` | scdn 国家代码参数 |
| `-t, --timeout` | 验证超时秒数 |
| `--no-verify` | 跳过验证 |
| `--no-save` | 不保存文件 |
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
