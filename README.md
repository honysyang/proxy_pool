# Proxy Pool

自动收集、验证、保存并输出代理 IP 池。池子文件格式为 JSON，按 `ip:port` 为键去重。

所有 IP 提取源统一放在 `scripts/sources/` 下，由 `scripts/fetch_all.py` 调度，CLI 对外提供统一操作。

## 项目结构

```text
proxy_pool_project/
├── scripts/
│   ├── fetch_all.py          # 统一调度多个源
│   └── sources/              # IP 提取源
│       ├── scdn.py
│       ├── proxymist.py
│       ├── zdaye.py
│       └── openclaw.py
├── proxy_pool/
│   ├── cli.py                # 对外统一 CLI
│   ├── checker.py            # 验证代理
│   └── storage.py            # JSON 存储/读取
├── demo/                     # 测试/验证示例
│   ├── echo_server.py        # 本地 echo API（记录访问者 IP）
│   ├── test_pool_hide_ip.py  # 验证代理是否隐藏真实 IP
│   └── local_proxy.py        # 最小化本地正向代理
├── skill/
│   └── SKILL.md              # Kimi Skill 说明
└── mcp_server.py             # MCP Server
```

## 安装依赖

```bash
cd proxy_pool_project
pip3 install requests 'requests[socks]' mcp
```

## 一键使用

```bash
cd proxy_pool_project

# 默认：收集 100 个 IP -> 验证 -> 保存 -> 输出
python3 -m proxy_pool.cli

# 收集 50 个 IP 到池子（会验证）
python3 -m proxy_pool.cli --target 50

# 只使用指定源
python3 -m proxy_pool.cli --sources scdn,proxymist

# 刷新池子：验证并移除无效 IP
python3 -m proxy_pool.cli --fresh

# 从池子快速输出 10 个 IP（不够则自动收集补足，不验证）
python3 -m proxy_pool.cli --output-count 10

# JSON 格式输出
python3 -m proxy_pool.cli --output-count 10 --json

# 使用池子中的随机代理去收集新 IP（失败自动回退直连）
python3 -m proxy_pool.cli --target 100 --use-pool-proxy
```

## CLI 参数

| 参数 | 说明 |
|------|------|
| `--target` | 收集 N 个 IP 到池子（默认 100，会验证） |
| `--sources` | 指定源，逗号分隔 |
| `-o, --output` | 池子文件路径（默认 `proxy_pool.json`） |
| `-p, --protocol` | scdn 协议参数（`http`/`https`/`socks4`/`socks5`/`all`） |
| `--country-code` | scdn 国家代码参数 |
| `-t, --timeout` | 验证超时秒数 |
| `--no-verify` | `--target` 收集后跳过验证 |
| `--use-pool-proxy` | 使用池子中的随机代理进行收集，失败自动回退直连 |
| `--fresh` | 验证现有池子，移除无效 IP |
| `--output-count` | 从池子输出 N 个 IP，不够则自动收集补足 |
| `--json` | JSON 数组格式输出 |

## 新增信息源

1. 在 `scripts/sources/` 新建 `.py`
2. 实现 `fetch(limit=20, proxy=None)`，返回 `ip:port` 列表
3. 在 `scripts/fetch_all.py` 的 `SOURCES` 中注册

示例：

```python
# scripts/sources/my_source.py
import requests

URL = "https://example.com/proxies"


def _proxies(proxy):
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return {"http": proxy, "https": proxy}


def fetch(limit=20, proxy=None):
    resp = requests.get(URL, proxies=_proxies(proxy), timeout=15)
    resp.raise_for_status()
    return ["1.2.3.4:8080", "5.6.7.8:3128"]
```

## 读取 IP 池

```python
from proxy_pool.storage import load_ips

ips = load_ips("proxy_pool.json")
```

## 验证代理是否隐藏了真实 IP

项目提供了测试 demo：

```bash
# 1. 确保池子里有代理
python3 -m proxy_pool.cli --target 20 --sources scdn --no-verify

# 2. 用公开 echo 服务验证
python3 demo/test_pool_hide_ip.py --target-url https://httpbin.org/ip --count 5
```

如果输出中代理返回的 `origin` 与 `[DIRECT]` 不同，说明本机真实 IP 已被隐藏。

也可以自己部署 echo API 到公网服务器（或使用 ngrok 暴露本地服务），然后：

```bash
python3 demo/test_pool_hide_ip.py --target-url http://你的公网地址:5000/ip --count 5
```

> 注意：公开代理通常无法访问 `127.0.0.1` 或 `192.168.x.x` 等私网地址。要验证私网目标的代理转发，可使用 `demo/local_proxy.py` 在私网内另起一台代理。

## MCP Server

```bash
python3 mcp_server.py
```

暴露工具：
- `collect_proxies`：收集 IP
- `fresh_proxies`：验证本地池
- `output_proxies`：从本地池输出 N 个 IP（不够则收集补足）
- `load_proxies`：读取本地池

## Kimi Skill

将 `skill/` 目录注册为 Kimi Skill 后，可直接通过自然语言调用本项目 CLI。

## 关于 openclaw

`scripts/sources/openclaw.py` 仅用于统计/安全研究，不作为代理源。

## 注意事项

- 免费代理池质量不稳定，可能会出现连接超时、403、SSL 错误等，属于正常现象。
- 建议先用 `--fresh` 验证并清理无效 IP，再用于实际请求。
- 验证默认访问 `baidu.com`，某些代理对国内站可用但无法访问国外目标，需结合实际目标测试。
