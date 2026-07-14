# Agent 指南

## 项目概述

代理池管理项目，基于 [proxy.scdn.io API 文档](https://proxy.scdn.io/api_docs.php)。

核心模块：

1. `proxy_pool/api.py`：调用 `proxy.scdn.io/api/get_proxy.php`。
   - 支持参数：`protocol`（http/https/socks4/socks5/all）、`count`（1-20）、`country_code`（如 CN、US）。
   - 返回结构：`{"code": 200, "message": "success", "data": {"proxies": ["ip:port"], "count": N}}`。
2. `proxy_pool/checker.py`：通过访问 `www.baidu.com` 验证代理。
   - `protocol=all` 时默认用 `http` 尝试验证。
   - SOCKS 代理依赖 `requests[socks]`。
3. `proxy_pool/storage.py`：保存/读取代理，支持 JSON 字典（自动去重）和 TXT 列表。
4. `proxy_pool/cli.py`：命令行入口。
5. `mcp_server.py`：MCP Server，stdio 运行。
6. `skill/SKILL.md`：Kimi Skill 定义。

## 开发规范

- 保持模块单一职责。
- 新增协议或 API 参数时，同步更新 `VALID_PROTOCOLS`、`cli.py`、`mcp_server.py`、`skill/SKILL.md`。
- JSON 保存格式以 `IP:port` 为 key，天然去重。

## 测试

```bash
cd proxy_pool_project
python3 -m pytest tests/ -q
```

## 运行

```bash
# CLI
python3 -m proxy_pool.cli -c 10

# MCP Server
python3 mcp_server.py
```
