# Agent 指南

## 项目概述

极简代理池项目，对外只通过 CLI 提供统一入口，池子文件为 JSON。

CLI 三种核心操作：
- `--target N`：收集 N 个 IP 到池子（默认验证）
- `--fresh`：验证现有池子，移除无效 IP
- `--output-count N`：从池子输出 N 个 IP，不够则自动收集补足

内部流程：
1. `proxy_pool/cli.py` 解析参数
2. 调用 `scripts/fetch_all.py` 收集 IP
3. `proxy_pool/checker.py` 验证代理
4. `proxy_pool/storage.py` 保存/读取 JSON 池

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`
2. 实现 `fetch(limit=20, proxy=None) -> list[str]`，返回 `ip:port` 列表；`proxy` 为 `ip:port` 字符串，可选
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

# 刷新池子
python3 -m proxy_pool.cli --fresh

# 快速输出 10 个
python3 -m proxy_pool.cli --output-count 10

# 使用池子中的随机代理进行收集（失败自动回退直连）
python3 -m proxy_pool.cli --target 100 --use-pool-proxy

# MCP Server
python3 mcp_server.py
```
