#!/usr/bin/env python3
"""Proxy Pool MCP Server。

以 stdio 方式运行，暴露以下工具：
- fetch_proxies: 从代理 API 获取代理
- check_proxies: 验证一组代理是否可用
- save_proxies: 保存代理到本地文件
- load_proxies: 从本地文件读取代理
"""

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from proxy_pool.api import DEFAULT_API, MAX_COUNT, VALID_PROTOCOLS, fetch_proxies
from proxy_pool.checker import build_proxy_dict, check_proxy
from proxy_pool.storage import load_ips, save_ips

app = Server("proxy-pool")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch_proxies",
            description="从 proxy.scdn.io API 获取代理列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_url": {"type": "string", "description": "代理 API 地址", "default": DEFAULT_API},
                    "protocol": {
                        "type": "string",
                        "enum": list(VALID_PROTOCOLS),
                        "description": "代理协议类型",
                        "default": "http",
                    },
                    "count": {
                        "type": "integer",
                        "description": f"获取数量，1-{MAX_COUNT}",
                        "default": 5,
                    },
                    "country_code": {
                        "type": "string",
                        "description": "ISO 3166-1 两位国家代码，如 CN、US",
                        "default": None,
                    },
                },
            },
        ),
        Tool(
            name="check_proxies",
            description="验证一组代理是否能访问百度",
            inputSchema={
                "type": "object",
                "properties": {
                    "proxies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "代理地址列表，如 [\"1.2.3.4:8080\", \"socks5://5.6.7.8:1080\"]",
                    },
                    "protocol": {
                        "type": "string",
                        "enum": list(VALID_PROTOCOLS),
                        "description": "代理协议类型（all 时默认用 http 验证）",
                        "default": "http",
                    },
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 8},
                    "workers": {"type": "integer", "description": "并发数", "default": 10},
                },
                "required": ["proxies"],
            },
        ),
        Tool(
            name="save_proxies",
            description="保存代理列表到本地文件（JSON 字典格式，自动去重）",
            inputSchema={
                "type": "object",
                "properties": {
                    "proxies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "代理地址列表",
                    },
                    "output_file": {"type": "string", "description": "输出文件路径", "default": "proxy_pool.json"},
                    "protocol": {
                        "type": "string",
                        "enum": list(VALID_PROTOCOLS),
                        "description": "代理协议类型",
                        "default": "http",
                    },
                    "format": {"type": "string", "enum": ["json", "txt"], "default": "json"},
                    "dedup": {"type": "boolean", "description": "是否去重", "default": True},
                },
                "required": ["proxies"],
            },
        ),
        Tool(
            name="load_proxies",
            description="从本地文件读取代理列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file": {"type": "string", "description": "输入文件路径", "default": "proxy_pool.json"},
                },
                "required": ["input_file"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fetch_proxies":
        result = _fetch(arguments)
    elif name == "check_proxies":
        result = _check(arguments)
    elif name == "save_proxies":
        result = _save(arguments)
    elif name == "load_proxies":
        result = _load(arguments)
    else:
        raise ValueError(f"未知工具: {name}")

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _fetch(arguments: dict):
    api_url = arguments.get("api_url", DEFAULT_API)
    protocol = arguments.get("protocol", "http")
    count = arguments.get("count", 5)
    country_code = arguments.get("country_code")
    raw = fetch_proxies(api_url, protocol, count, country_code)
    proxy_urls = []
    for item in raw:
        pd = build_proxy_dict(item, protocol)
        if pd:
            proxy_urls.append(pd.get(list(pd.keys())[0]))
    return {"count": len(proxy_urls), "protocol": protocol, "proxies": proxy_urls}


def _check(arguments: dict):
    proxies = arguments.get("proxies", [])
    protocol = arguments.get("protocol", "http")
    timeout = arguments.get("timeout", 8)
    workers = arguments.get("workers", 10)

    proxy_dicts = []
    for p in proxies:
        pd = build_proxy_dict(p, protocol)
        if pd:
            proxy_dicts.append(pd)

    working = []
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_proxy = {executor.submit(check_proxy, p, timeout): p for p in proxy_dicts}
        for future in as_completed(future_to_proxy):
            proxies, latency, status = future.result()
            proxy_url = proxies.get(list(proxies.keys())[0])
            if latency is not None:
                working.append({"proxy": proxy_url, "latency_ms": latency, "status": status})
            else:
                failed.append(proxy_url)

    return {"total": len(proxy_dicts), "working": working, "failed": failed}


def _save(arguments: dict):
    proxies = arguments.get("proxies", [])
    output_file = arguments.get("output_file", "proxy_pool.json")
    protocol = arguments.get("protocol", "http")
    format = arguments.get("format", "json")
    dedup = arguments.get("dedup", True)

    saved = save_ips(output_file, proxies, protocol=protocol, dedup=dedup, format=format)
    return {"saved_count": len(saved), "output_file": os.path.abspath(output_file), "proxies": saved}


def _load(arguments: dict):
    input_file = arguments.get("input_file", "proxy_pool.json")
    proxies = load_ips(input_file)
    return {"count": len(proxies), "proxies": proxies}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
