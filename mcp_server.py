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
CLI = os.path.join(BASE_DIR, "proxy_pool", "cli.py")

app = Server("proxy-pool")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="collect_proxies",
            description="收集指定数量的代理 IP 到本地 JSON 池。默认直接请求源站，只有 use_pool_proxy=true 时才会用池子中的随机代理去收集（失败自动回退直连）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_count": {"type": "integer", "default": 100},
                    "sources": {"type": "string", "description": "逗号分隔的源列表"},
                    "output_file": {"type": "string", "default": "proxy_pool.json"},
                    "protocol": {"type": "string", "default": "http"},
                    "country_code": {"type": "string"},
                    "no_verify": {"type": "boolean", "default": False},
                    "use_pool_proxy": {"type": "boolean", "default": False, "description": "是否使用池子中的随机代理进行收集"},
                    "workers": {"type": "integer", "default": 4, "description": "并发源数"},
                },
            },
        ),
        Tool(
            name="fresh_proxies",
            description="验证本地 JSON 代理池，移除连接超时或不可用的 IP，返回验证结果摘要。",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_file": {"type": "string", "default": "proxy_pool.json"},
                    "timeout": {"type": "integer", "default": 8},
                },
            },
        ),
        Tool(
            name="output_proxies",
            description="从本地 JSON 代理池输出指定数量的 IP。如果池子不足，会自动收集补足。可指定输出为 JSON 数组格式方便程序解析。",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_count": {"type": "integer"},
                    "sources": {"type": "string", "description": "逗号分隔的源列表"},
                    "output_file": {"type": "string", "default": "proxy_pool.json"},
                    "protocol": {"type": "string", "default": "http"},
                    "country_code": {"type": "string"},
                    "use_pool_proxy": {"type": "boolean", "default": False, "description": "是否使用池子中的随机代理进行收集补足"},
                    "json_output": {"type": "boolean", "default": False, "description": "是否以 JSON 数组格式输出"},
                    "workers": {"type": "integer", "default": 4, "description": "并发源数"},
                },
                "required": ["output_count"],
            },
        ),
        Tool(
            name="load_proxies",
            description="读取本地 JSON 代理池，返回当前所有 IP 列表及总数。",
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
    elif name == "fresh_proxies":
        result = _fresh(arguments)
    elif name == "output_proxies":
        result = _output(arguments)
    elif name == "load_proxies":
        result = _load(arguments)
    else:
        raise ValueError(f"未知工具: {name}")
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _build_cli_cmd(args_list):
    return ["python3", CLI] + args_list


def _run_cli(args_list):
    cmd = _build_cli_cmd(args_list)
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        return {"status": "error", "message": result.stderr or result.stdout}
    return {"status": "ok", "output": result.stdout}


def _collect(arguments: dict):
    output = arguments.get("output_file", "proxy_pool.json")
    cmd = [
        "--target", str(arguments.get("target_count", 100)),
        "--output", output,
        "--protocol", arguments.get("protocol", "http"),
    ]
    if arguments.get("sources"):
        cmd.extend(["--sources", arguments["sources"]])
    if arguments.get("country_code"):
        cmd.extend(["--country-code", arguments["country_code"]])
    if arguments.get("no_verify"):
        cmd.append("--no-verify")
    if arguments.get("use_pool_proxy"):
        cmd.append("--use-pool-proxy")
    cmd.extend(["--workers", str(arguments.get("workers", 4))])
    return _run_cli(cmd)


def _fresh(arguments: dict):
    output = arguments.get("output_file", "proxy_pool.json")
    return _run_cli(["--fresh", "--output", output, "--timeout", str(arguments.get("timeout", 8))])


def _output(arguments: dict):
    output = arguments.get("output_file", "proxy_pool.json")
    cmd = [
        "--output-count", str(arguments["output_count"]),
        "--output", output,
        "--protocol", arguments.get("protocol", "http"),
    ]
    if arguments.get("sources"):
        cmd.extend(["--sources", arguments["sources"]])
    if arguments.get("country_code"):
        cmd.extend(["--country-code", arguments["country_code"]])
    if arguments.get("use_pool_proxy"):
        cmd.append("--use-pool-proxy")
    if arguments.get("json_output"):
        cmd.append("--json")
    cmd.extend(["--workers", str(arguments.get("workers", 4))])
    return _run_cli(cmd)


def _load(arguments: dict):
    input_file = arguments.get("input_file", "proxy_pool.json")
    ips = load_ips(input_file)
    return {"count": len(ips), "proxies": ips}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
