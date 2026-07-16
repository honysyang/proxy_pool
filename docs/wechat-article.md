# 一个极简的 Python 代理池：从收集到验证，一条命令搞定

> 做爬虫、安全测试或数据采集时，代理 IP 是最常用的“基础设施”之一。但免费代理来源分散、质量参差不齐，管理和验证都很麻烦。本文介绍一个开源的 Python 代理池项目，用一条命令完成收集、验证、刷新和输出。

---

## 01 为什么需要代理池

在实际业务中，我们经常遇到这些问题：

- 爬虫请求频繁，目标站对单一 IP 限流或封禁；
- 网上找到的代理列表来源多、格式乱，不好统一管理；
- 拿到一批代理后，不知道哪些还活着、哪些已经失效；
- 想用代理隐藏真实 IP，却不知道请求是否真的走了代理。

一个合格的代理池，至少要解决三件事：**多源聚合、自动验证、方便取用**。

---

## 02 项目定位

这是一个面向个人开发者和小团队的轻量级代理池，核心特点：

- **统一 CLI 入口**：收集、验证、刷新、输出，全部一条命令完成；
- **JSON 池子格式**：按 `ip:port` 去重，便于程序读取；
- **多源并发收集**：内置 scdn、proxymist、zdaye 等来源，支持并发抓取；
- **自动验证**：收集后默认验证，剔除无效 IP；
- **代理轮换收集**：可用池子中的代理去抓取新代理，降低本机 IP 暴露风险；
- **MCP / Kimi Skill 支持**：方便接入智能体工作流。

---

## 03 一分钟上手

```bash
cd proxy_pool_project
pip3 install requests 'requests[socks]' mcp

# 默认收集 100 个 IP，自动验证
python3 -m proxy_pool.cli

# 快速输出 10 个代理
python3 -m proxy_pool.cli --output-count 10

# 刷新池子，移除失效 IP
python3 -m proxy_pool.cli --fresh
```

收集结果保存在 `proxy_pool.json`，结构如下：

```json
{
  "8.221.141.88:8080": {"source": "scdn", "updated_at": "2026-07-15T12:00:00"},
  "47.100.130.127:8080": {"source": "zdaye", "updated_at": "2026-07-15T12:00:01"}
}
```

---

## 04 架构设计

```text
proxy_pool_project/
├── scripts/sources/      # 各个代理来源
├── scripts/fetch_all.py  # 统一调度、并发收集
├── proxy_pool/
│   ├── cli.py            # 统一命令行入口
│   ├── checker.py        # 代理验证
│   └── storage.py        # JSON 读写
├── mcp_server.py         # MCP Server
└── skill/SKILL.md        # Kimi Skill
```

**收集流程**：

1. `cli.py` 解析参数；
2. 调用 `fetch_all.py`，按配置的并发数（默认 4）同时抓取多个源；
3. 新 IP 写入 `proxy_pool.json` 并去重；
4. 默认进入 `checker.py` 验证，移除无效 IP；
5. 输出可用代理列表。

---

## 05 几个实用场景

### 场景一：爬虫自动换代理

```python
import requests
from proxy_pool.storage import load_ips

ips = load_ips("proxy_pool.json")
proxy = f"http://{ips[0]}"

requests.get(
    "https://example.com/api",
    proxies={"http": proxy, "https": proxy},
    timeout=15,
)
```

### 场景二：验证代理是否隐藏了真实 IP

```bash
python3 demo/test_pool_hide_ip.py \
    --target-url https://httpbin.org/ip \
    --count 5
```

如果代理返回的 `origin` 与直连不同，说明请求确实走了代理。

### 场景三：接入智能体

通过 MCP Server 或 Kimi Skill，智能体可以直接调用 `collect_proxies`、`fresh_proxies`、`output_proxies` 等工具，无需手写命令。

---

## 06 最佳实践

1. **多收集一些**：免费代理失效快，建议 `--target 200` 起步；
2. **使用前验证**：`python3 -m proxy_pool.cli --fresh`；
3. **结合目标测试**：默认验证访问 baidu.com，不代表能访问你的目标站；
4. **脚本化输出**：`--output-count 20 --json > proxies.json`；
5. **生产环境用付费代理**：免费池适合临时/测试，长期稳定业务建议接入付费代理。

---

## 07 结语

代理池的本质是“用工程化的方式管理不确定性”。这个项目没有追求功能最全，而是把最常用的路径做到最简单：一条命令，拿到可用的代理。

如果你也在为代理 IP 的管理头疼，不妨试试这个项目。

**项目地址**：https://gitee.com/yzj1/proxy_pool
