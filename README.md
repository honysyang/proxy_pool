# Proxy Pool

获取、验证并管理代理 IP 池。所有 IP 提取源统一放在 `scripts/sources/` 下，由 `scripts/fetch_all.py` 统一调度。

## 项目结构

```text
proxy_pool_project/
├── scripts/
│   ├── fetch_all.py          # 统一调度入口
│   └── sources/              # IP 提取源
│       ├── scdn.py           # API 提取
│       ├── proxymist.py      # 网页爬取
│       ├── zdaye.py          # 网页爬取
│       └── openclaw.py       # 统计收集（非代理）
├── proxy_pool/               # 核心功能：验证、存储、读取
├── mcp_server.py             # MCP Server
└── skill/SKILL.md            # Kimi Skill
```

## 快速开始

### 1. 收集 IP

```bash
# 收集 100 个新 IP 到 proxy_pool.json
python3 scripts/fetch_all.py --target 100

# 只使用指定源
python3 scripts/fetch_all.py --target 100 --sources scdn,proxymist

# 指定 scdn 协议和国家
python3 scripts/fetch_all.py --target 100 --protocol http --country-code US
```

### 2. 验证 IP

```bash
python3 -m proxy_pool.cli verify
```

### 3. 查看 IP 列表

```bash
python3 -m proxy_pool.cli list
```

## 新增信息源

在 `scripts/sources/` 下新建一个 `.py` 文件，实现 `fetch(limit)` 函数，返回 `ip:port` 列表：

```python
# scripts/sources/my_source.py
import requests

URL = "https://example.com/proxies"


def fetch(limit=20):
    resp = requests.get(URL, timeout=15)
    return ["1.2.3.4:8080", "5.6.7.8:3128"]
```

然后在 `scripts/fetch_all.py` 的 `SOURCES` 字典中注册：

```python
from scripts.sources import my_source

SOURCES = {
    ...
    "my_source": my_source,
}
```

## CLI

```bash
# 收集
python3 -m proxy_pool.cli collect --target 100

# 验证
python3 -m proxy_pool.cli verify

# 列出
python3 -m proxy_pool.cli list --json
```

## MCP Server

```bash
python3 mcp_server.py
```

暴露工具：
- `collect_proxies`：收集 IP
- `verify_proxies`：验证本地池
- `load_proxies`：读取本地池

### MCP JSON 配置

```json
{
  "mcpServers": {
    "proxy-pool": {
      "command": "python3",
      "args": [
        "/home/kali/proxy_pool_project/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/kali/proxy_pool_project"
      }
    }
  }
}
```

## 关于 openclaw

`scripts/sources/openclaw.py` 用于从 `https://openclaw.allegro.earth/` 收集暴露实例 IP:端口，**仅用于统计/安全研究，不作为代理使用**。

```bash
python3 scripts/fetch_all.py --target 1000 --sources openclaw
```
