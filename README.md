# Proxy Pool

从 [proxy.scdn.io](https://proxy.scdn.io/api_docs.php) 获取代理，通过百度验证可用性，并以 JSON/TXT 格式保存去重后的 IP。

## 安装

```bash
cd proxy_pool_project
pip install -e .
```

## 命令行

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

## 作为 Python 模块

```bash
python3 -m proxy_pool.cli -c 5
```

## MCP Server

以 stdio 方式启动：

```bash
python3 mcp_server.py
```

暴露工具：`fetch_proxies`、`check_proxies`、`save_proxies`、`load_proxies`。

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
