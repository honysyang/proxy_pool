"""命令行入口（简单包装）。"""

import argparse
import json
import os
import subprocess
import sys

from .checker import check_proxy
from .storage import extract_ip_port, load_ips


def _run_collect(args):
    """调用 scripts/fetch_all.py 收集 IP。"""
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "fetch_all.py")
    cmd = [
        "python3", script,
        "--target", str(args.target),
        "--output", args.output,
        "--protocol", args.protocol,
    ]
    if args.sources:
        cmd.extend(["--sources", args.sources])
    if args.country_code:
        cmd.extend(["--country-code", args.country_code])

    subprocess.run(cmd, check=True)


def _run_verify(args):
    """验证本地池中的代理。"""
    ips = load_ips(args.output)
    print(f"[*] 开始验证 {len(ips)} 个代理...")
    working = 0
    failed = 0
    for ip in ips:
        protocol = "http"
        pd = {protocol: f"{protocol}://{ip}"}
        _, latency, status = check_proxy(pd, timeout=args.timeout)
        if latency is not None:
            print(f"[OK] {ip:<30} 延迟: {latency:>4}ms 状态码: {status}")
            working += 1
        else:
            print(f"[FAIL] {ip}")
            failed += 1
    print(f"\n[*] 验证完成：{working}/{len(ips)} 可用")


def _run_list(args):
    """列出本地池中的 IP。"""
    ips = load_ips(args.output)
    if args.json:
        print(json.dumps(ips, ensure_ascii=False, indent=2))
    else:
        for ip in ips:
            print(ip)
    print(f"\n[*] 共 {len(ips)} 条")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Proxy Pool: 收集、验证、读取代理 IP")
    sub = parser.add_subparsers(dest="command", help="子命令")

    # collect
    p_collect = sub.add_parser("collect", help="收集 IP 到本地 JSON 池")
    p_collect.add_argument("--target", type=int, default=100, help="目标数量（默认 100）")
    p_collect.add_argument("--sources", default=None, help="指定源，逗号分隔")
    p_collect.add_argument("-o", "--output", default="proxy_pool.json", help="输出文件")
    p_collect.add_argument("-p", "--protocol", default="http", help="scdn 协议参数")
    p_collect.add_argument("--country-code", default=None, help="scdn 国家代码参数")

    # verify
    p_verify = sub.add_parser("verify", help="验证本地池中的代理")
    p_verify.add_argument("-o", "--output", default="proxy_pool.json", help="输入文件")
    p_verify.add_argument("-t", "--timeout", type=int, default=8, help="超时秒数")

    # list
    p_list = sub.add_parser("list", help="列出本地池中的 IP")
    p_list.add_argument("-o", "--output", default="proxy_pool.json", help="输入文件")
    p_list.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args(argv)

    if args.command == "collect":
        _run_collect(args)
    elif args.command == "verify":
        _run_verify(args)
    elif args.command == "list":
        _run_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
