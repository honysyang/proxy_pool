# Proxy Pool

获取、验证并管理代理 IP 池，支持 HTTP/HTTPS/SOCKS4/SOCKS5 协议，以 JSON/TXT 格式保存去重后的 IP。

默认内置 `scdn` 提供商（proxy.scdn.io），支持通过 Provider 模式扩展更多代理源。

## 安装

Kali 等系统的 Python 受 PEP 668 保护，建议先创建虚拟环境：

```bash
cd proxy_pool_project
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

或者直接用 `--break-system-packages`（不推荐）：

```bash
pip install -e . --break-system-packages
```

## 命令行

安装后使用 `proxy-pool` 命令：

```bash
# 获取并验证 10 个 http 代理，保存到 proxy_pool.json
proxy-pool -c 10 -t 10

# 获取 5 个中国 HTTPS 代理
proxy-pool -p https --country-code CN -c 5

# 获取 3 个 SOCKS5 代理
proxy-pool -p socks5 -c 3

# 获取任意类型代理（protocol=all）
proxy-pool -p all -c 10

# 快速获取 20 个代理（不验证）
proxy-pool -c 20 -q

# 保存为 txt
proxy-pool -c 10 -f txt -o proxies.txt
```

不安装也可直接运行：

```bash
python3 -m proxy_pool.cli -c 5
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-p, --protocol` | 协议：`http`、`https`、`socks4`、`socks5`、`all`（默认 http） |
| `-c, --count` | 获取数量，1-20（默认 5） |
| `--country-code` | ISO 3166-1 两位国家代码，如 `CN`、`US` |
| `-t, --timeout` | 验证超时秒数 |
| `-o, --output` | 输出文件路径 |
| `-f, --format` | 输出格式：`json`（默认）、`txt` |
| `-q, --quick` | 快速模式，不验证 |
| `--save-all` | 保存所有获取到的代理 |
| `--provider` | 指定代理提供商名称 |

## 扩展代理源

在 `proxy_pool/providers/` 下新建模块，继承 `BaseProvider` 并实现 `fetch` 方法，然后在 `proxy_pool/providers/__init__.py` 中注册即可。

示例结构：

```python
# proxy_pool/providers/my_source.py
from .base import BaseProvider

class MySourceProvider(BaseProvider):
    name = "my_source"
    default_api_url = "https://example.com/api"

    def fetch(self, protocol="http", count=5, country_code=None):
        # 实现获取逻辑
        return ["1.2.3.4:8080"]
```

## 作为 Python 模块

```bash
python3 -m proxy_pool.cli -c 5
```

## MCP Server

以 stdio 方式启动：

```bash
python3 mcp_server.py
```

暴露工具：`fetch_proxies`（支持 `provider`、`protocol`、`count`、`country_code`）、`check_proxies`、`save_proxies`、`load_proxies`。

### MCP JSON 配置

标准 MCP 配置格式如下：

注册新代理源后，可通过 `--provider` 参数或 MCP 的 `provider` 字段切换源。

#### 方式一：虚拟环境安装后调用（推荐）

```json
{
  "mcpServers": {
    "proxy-pool": {
      "command": "/home/kali/proxy_pool_project/.venv/bin/proxy-pool-mcp"
    }
  }
}
```

#### 方式二：不安装，直接指定脚本

```json
{
  "mcpServers": {
    "proxy-pool": {
      "command": "python3",
      "args": [
        "/home/kali/proxy_pool_project/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/kali/proxy_pool_project"
      }
    }
  }
}
```

### 各客户端配置位置

- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **VS Code (Cline / Roo)**: 插件 MCP 设置中粘贴 JSON
- **Kimi Code CLI**: MCP 设置中添加 `proxy-pool` server

## 输出格式

默认保存为 JSON 字典，key 为 `IP:port`，value 包含协议、延迟、状态码、更新时间：

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
