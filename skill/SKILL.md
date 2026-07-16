---
name: proxy-pool
description: 当用户需要代理 IP 时，统一收集、验证、刷新、输出代理池。支持通过 CLI 或 MCP 调用。
---

# Proxy Pool

本项目用于自动收集、验证并输出代理 IP 池，池子文件为 JSON。对外入口是 `proxy_pool/cli.py` 和 `mcp_server.py`。

## 什么时候使用本 Skill

只要用户提到以下任意需求，就应该调用本工具：

- “给我一些代理 IP”
- “收集代理” / “爬代理” / “获取代理池”
- “验证代理是否可用”
- “输出 N 个代理” / “给我 10 个 IP”
- “刷新代理池” / “清理无效代理”
- “用代理隐藏 IP” / “验证代理是否隐藏了我的真实 IP”

## 推荐调用方式

默认先收集再验证：

```bash
cd /home/kali/proxy_pool_project
python3 -m proxy_pool.cli --target 100
```

如果只需要快速拿 N 个代理（不验证）：

```bash
python3 -m proxy_pool.cli --output-count 10
```

如果用户明确要求验证现有池子：

```bash
python3 -m proxy_pool.cli --fresh
```

如果用户想避免暴露本机 IP 去收集：

```bash
python3 -m proxy_pool.cli --target 100 --use-pool-proxy
```

## 核心参数速查

| 参数 | 用途 | 默认值 |
|------|------|--------|
| `--target N` | 收集 N 个 IP 并验证 | 100 |
| `--output-count N` | 从池子输出 N 个 IP，不够则自动收集补足 | 无 |
| `--fresh` | 验证并清理无效 IP | 无 |
| `--sources a,b` | 指定来源，如 `scdn,proxymist` | 全部 |
| `-p http/socks5` | scdn 协议类型 | `http` |
| `--use-pool-proxy` | 用池子中的随机代理去收集（失败回退直连） | 不启用 |
| `--workers` | 并发源数 | 4 |
| `--json` | 输出 JSON 数组格式 | 无 |

> 默认收集时**直接请求源站**，不会走代理。只有显式加上 `--use-pool-proxy` 才会使用池子中的代理。

## MCP 调用

配置示例：

```json
{
  "mcpServers": {
    "proxy-pool": {
      "command": "python3",
      "args": ["/home/kali/proxy_pool_project/mcp_server.py"]
    }
  }
}
```

可用工具：
- `collect_proxies`：收集 IP 到本地池
- `fresh_proxies`：验证并清理本地池
- `output_proxies`：从本地池输出 N 个 IP（不够则收集补足）
- `load_proxies`：读取本地池中的 IP 列表

调用示例：

```json
{
  "name": "collect_proxies",
  "arguments": {
    "target_count": 50,
    "sources": "scdn",
    "protocol": "http",
    "use_pool_proxy": false,
    "workers": 4
  }
}
```

## 验证代理是否隐藏真实 IP

```bash
python3 -m proxy_pool.cli --target 20 --sources scdn --no-verify
python3 demo/test_pool_hide_ip.py --target-url https://httpbin.org/ip --count 5
```

## 注意事项

- 免费代理不稳定，收集后建议验证（默认会验证）。
- 验证默认访问 `baidu.com`，某些代理对国内站通、国外站不通，需结合目标测试。
- 公开代理通常无法访问 `127.0.0.1` 或 `192.168.x.x` 等私网地址。
