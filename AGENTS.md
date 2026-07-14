# Agent 指南

## 项目概述

通用代理池管理项目：获取、验证、保存代理 IP。

核心模块：

1. `proxy_pool/api.py`：代理 API 统一入口，通过 Provider 模式分发。
   - 默认 `scdn` 提供商。
   - 新增代理源：继承 `proxy_pool/providers/base.py` 中的 `BaseProvider`，在 `proxy_pool/providers/__init__.py` 注册。
2. `proxy_pool/providers/`
   - `base.py`: `BaseProvider` 抽象基类
   - `scdn.py`: scdn.io 提供商实现
   - `__init__.py`: 提供商注册表
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
