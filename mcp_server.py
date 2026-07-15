#!/usr/bin/env python3
"""Proxy Pool MCP Server（简化版）。"""

import asyncio
import json
import os
import subprocess
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from proxy_pool.checker import check_proxy
from proxy_pool.storage import load_ips

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH_ALL = os.path.join(BASE_DIR, "scripts", "fetch_all.py")

app = Server("proxy-pool")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="collect_proxies",
            description="收集指定数量的新唯一 IP 到本地 JSON 池",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_count": {"type": "integer", "default": 100},
                    "sources": {"type": "string", "description": "逗号分隔的源列表"},
                    "output_file": {"type": "string", "default": "proxy_pool.json"},
                    "protocol": {"type": "string", "default": "http"},
                    "country_code": {"type": "string"},
                },
            },
        ),
        Tool(
            name="verify_proxies",
            description="验证本地 JSON 池中代理的可用性",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file": {"type": "string", "default": "proxy_pool.json"},
                    "timeout": {"type": "integer", "default": 8},
                },
            },
        ),
        Tool(
            name="load_proxies",
            description="读取本地 JSON 池中的 IP 列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file": {"type": "string", "default": "proxy_pool.json"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "collect_proxies":
        result = _collect(arguments)
    elif name == "verify_proxies":
        result = _verify(arguments)
    elif name == "load_proxies":
        result = _load(arguments)
    else:
        raise ValueError(f"未知工具: {name}")
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _collect(arguments: dict):
    cmd = [
        "python3", FETCH_ALL,
        "--target", str(arguments.get("target_count", 100)),
        "--output", arguments.get("output_file", "proxy_pool.json"),
        "--protocol", arguments.get("protocol", "http"),
    ]
    if arguments.get("sources"):
        cmd.extend(["--sources", arguments["sources"]])
    if arguments.get("country_code"):
        cmd.extend(["--country-code", arguments["country_code"]])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"status": "ok", "message": "收集完成"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr or e.stdout}


def _verify(arguments: dict):
    input_file = arguments.get("input_file", "proxy_pool.json")
    timeout = arguments.get("timeout", 8)
    ips = load_ips(input_file)

    working = []
    failed = []
    for ip in ips:
        pd = {"http": f"http://{ip}"}
        _, latency, status = check_proxy(pd, timeout=timeout)
        if latency is not None:
            working.append({"proxy": ip, "latency_ms": latency, "status": status})
        else:
            failed.append(ip)

    return {"total": len(ips), "working": working, "failed": failed}


def _load(arguments: dict):
    input_file = arguments.get("input_file", "proxy_pool.json")
    ips = load_ips(input_file)
    return {"count": len(ips), "proxies": ips}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
