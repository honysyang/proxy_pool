---
name: proxy-pool
description: 当用户需要获取、验证、保存或管理 HTTP/HTTPS/SOCKS4/SOCKS5 代理 IP 池时，使用本项目中的 CLI 或 MCP 工具。支持多代理源扩展。
---

# Proxy Pool

通用代理池工具：获取代理、验证可用性、以 JSON/TXT 保存去重后的 IP。默认内置 `scdn` 提供商，支持通过 Provider 模式扩展其他代理源。

## 何时使用

- 用户提到“代理池”、“爬代理”、“获取代理”、“验证代理”、“保存 IP”、“新增代理源”、“抓取网页代理”等。
- 需要按协议（http/https/socks4/socks5/all）或国家代码筛选代理。
- 需要从免费代理网站抓取 IP 并合并到本地 JSON 池。

## 项目位置

```
proxy_pool_project/
├── proxy_pool/
│   ├── providers/    # API 代理源提供商
│   ├── scrapers/     # 网页代理源抓取器
│   ├── aggregator.py # 聚合抓取结果到本地 JSON
│   ├── api.py        # API 统一入口
│   ├── checker.py    # 代理验证
│   ├── storage.py    # 存储与去重
│   └── cli.py        # 命令行入口
├── mcp_server.py     # MCP Server 入口
└── skill/SKILL.md    # 本文件
```

## API 参数

- `provider`: API 代理源名称，默认 `scdn`
- `protocol`: `http`、`https`、`socks4`、`socks5`、`all`（默认 `http`）
- `count`: 1-20（默认 1）
- `country_code`: ISO 3166-1 两位国家代码，如 `CN`、`US`

## 命令行用法

### API 获取模式

```bash
cd proxy_pool_project

# 获取并验证 10 个 http 代理
python3 -m proxy_pool.cli -c 10 -t 10

# 指定其他提供商（需先在 providers 中注册）
python3 -m proxy_pool.cli --provider scdn -c 10

# 获取 5 个中国 HTTPS 代理
python3 -m proxy_pool.cli -p https --country-code CN -c 5 -t 10

# 获取 3 个 SOCKS5 代理
python3 -m proxy_pool.cli -p socks5 -c 3 -t 10

# 任意类型代理（protocol=all），默认用 http 验证
python3 -m proxy_pool.cli -p all -c 10

# 快速获取 20 个代理（不验证）
python3 -m proxy_pool.cli -c 20 -q

# 保存为 txt
python3 -m proxy_pool.cli -c 10 -f txt
```

### 网页抓取模式

从免费代理网站爬取 IP 并合并到本地 `proxy_pool.json`：

```bash
# 爬取所有内置网页源
python3 -m proxy_pool.cli --scrape

# 只爬 proxymist
python3 -m proxy_pool.cli --scrape --sources proxymist

# 爬取并验证
python3 -m proxy_pool.cli --scrape --verify

# 每个源最多 10 条
python3 -m proxy_pool.cli --scrape --limit 10
```

当前内置网页源：`proxymist`、`zdaye`。

> 注意：`https://openclaw.allegro.earth/` 不是代理列表网站，而是暴露的 OpenClaw 实例监控面板，不适合作为代理源。

## 扩展代理源

新增代理源步骤：

1. 在 `proxy_pool/providers/` 新建模块，继承 `BaseProvider`
2. 实现 `fetch(self, protocol, count, country_code)` 方法
3. 在 `proxy_pool/providers/__init__.py` 中调用 `register_provider()`

示例：

```python
# proxy_pool/providers/my_source.py
from .base import BaseProvider

class MySourceProvider(BaseProvider):
    name = "my_source"
    default_api_url = "https://example.com/api"

    def fetch(self, protocol="http", count=5, country_code=None):
        # 调用 API 并返回 ["ip:port", ...]
        return ["1.2.3.4:8080"]
```

## MCP 工具

如果环境已注册 `mcp_server.py`，可直接调用：

- `fetch_proxies`: 从 API 拉取代理，支持 `provider`、`protocol`、`count`、`country_code`
- `scrape_proxies`: 从网页抓取代理并合并到本地 JSON，支持 `sources`、`limit`、`verify`
- `check_proxies`: 验证代理可用性
- `save_proxies`: 保存代理到文件
- `load_proxies`: 读取本地代理文件

## 输出格式

默认 JSON 字典，key 为 `IP:port`，value 含 `protocol`、`latency_ms`、`status`、`updated_at`：

```json
{
  "1.2.3.4:8080": {
    "protocol": "http",
    "latency_ms": 120,
    "status": 200,
    "updated_at": "2026-07-14T10:00:00"
  }
}
```

JSON 对象 key 天然去重，适合作为代理池持久化格式。
