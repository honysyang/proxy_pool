# Agent 指南

## 项目概述

极简代理池项目：

- `scripts/sources/*.py`：每个文件是一个 IP 提取源，必须实现 `fetch(limit)` 函数。
- `scripts/fetch_all.py`：统一调度所有源，收集、去重、保存到 JSON。
- `proxy_pool/`：核心功能包，只负责验证、存储、读取。
- `mcp_server.py`：MCP Server，暴露收集/验证/读取接口。
- `skill/SKILL.md`：Kimi Skill。

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py` 文件
2. 实现 `fetch(limit=20) -> list[str]`，返回 `ip:port` 列表
3. 在 `scripts/fetch_all.py` 的 `SOURCES` 字典中注册

## 测试

```bash
cd proxy_pool_project
python3 -m pytest tests/ -q
```

## 运行

```bash
# 收集 100 个 IP
python3 scripts/fetch_all.py --target 100

# CLI
python3 -m proxy_pool.cli collect --target 100
python3 -m proxy_pool.cli verify
python3 -m proxy_pool.cli list

# MCP Server
python3 mcp_server.py
```
