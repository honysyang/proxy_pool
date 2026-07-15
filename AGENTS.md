# Agent 指南

## 项目概述

极简代理池项目，对外只通过 CLI 提供统一入口：

```bash
python3 -m proxy_pool.cli
```

内部流程：
1. `proxy_pool/cli.py` 调用 `scripts/fetch_all.py`
2. `scripts/fetch_all.py` 调度 `scripts/sources/*.py` 收集 IP
3. `proxy_pool/checker.py` 验证代理可用性
4. `proxy_pool/storage.py` 保存/读取 JSON 池
5. CLI 输出最终 IP 列表

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`
2. 实现 `fetch(limit=20) -> list[str]`，返回 `ip:port` 列表
3. 在 `scripts/fetch_all.py` 的 `SOURCES` 中注册

## 测试

```bash
cd proxy_pool_project
python3 -m pytest tests/ -q
```

## 运行

```bash
# 一键：收集 -> 验证 -> 保存 -> 输出
python3 -m proxy_pool.cli

# 重新生成池子
python3 -m proxy_pool.cli --fresh

# 只输出前 10 个
python3 -m proxy_pool.cli --output-count 10

# MCP Server
python3 mcp_server.py
```
