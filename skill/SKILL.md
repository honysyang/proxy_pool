---
name: proxy-pool
description: 当用户需要从 proxy.scdn.io 获取、验证、保存或管理 HTTP/HTTPS/SOCKS4/SOCKS5 代理 IP 池时，使用本项目中的 CLI 或 MCP 工具。
---

# Proxy Pool

通用代理池工具：获取代理、验证可用性、以 JSON/TXT 保存去重后的 IP。默认内置 scdn 提供商，支持扩展其他代理源。

## 何时使用

- 用户提到“代理池”、“爬代理”、“获取代理”、“验证代理”、“保存 IP”等。
- 需要从 `proxy.scdn.io` 拉取代理并按协议、国家筛选。

## 项目位置

```
proxy_pool_project/
├── proxy_pool/       # Python 包
├── mcp_server.py     # MCP Server 入口
└── skill/SKILL.md    # 本文件
```

## API 参数

- `protocol`: `http`、`https`、`socks4`、`socks5`、`all`（默认 `http`）
- `count`: 1-20（默认 1）
- `country_code`: ISO 3166-1 两位国家代码，如 `CN`、`US`

## 命令行用法

```bash
cd proxy_pool_project

# 获取并验证 10 个 http 代理
python3 -m proxy_pool.cli -c 10 -t 10

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

## MCP 工具

如果环境已注册 `mcp_server.py`，可直接调用：

- `fetch_proxies`: 拉取代理，支持 `protocol`、`count`、`country_code`
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
