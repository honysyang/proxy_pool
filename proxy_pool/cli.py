"""统一 CLI 入口：自动收集、验证、保存并输出 IP 池。"""

import argparse
import json
import os
import subprocess
import sys

from .checker import check_proxy
from .storage import load_ips

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH_ALL = os.path.join(BASE_DIR, "scripts", "fetch_all.py")


def collect_ips(target, sources, output, protocol, country_code):
    """调用 scripts/fetch_all.py 收集 IP。"""
    cmd = [
        "python3", FETCH_ALL,
        "--target", str(target),
        "--output", output,
        "--protocol", protocol,
    ]
    if sources:
        cmd.extend(["--sources", sources])
    if country_code:
        cmd.extend(["--country-code", country_code])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] 收集失败: {result.stderr or result.stdout}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())


def verify_pool(output, timeout):
    """验证本地池中的代理。"""
    ips = load_ips(output)
    if not ips:
        print("[*] 池子为空，跳过验证")
        return []

    print(f"[*] 开始验证 {len(ips)} 个代理...")
    working = []
    failed = []
    for ip in ips:
        pd = {"http": f"http://{ip}"}
        _, latency, status = check_proxy(pd, timeout=timeout)
        if latency is not None:
            working.append({"proxy": ip, "latency_ms": latency, "status": status})
            print(f"[OK] {ip:<30} 延迟: {latency:>4}ms 状态码: {status}")
        else:
            failed.append(ip)
            print(f"[FAIL] {ip}")

    print(f"\n[*] 验证完成：{len(working)}/{len(ips)} 可用")
    return working


def output_pool(output, json_format):
    """输出本地池中的 IP。"""
    ips = load_ips(output)
    if json_format:
        print(json.dumps(ips, ensure_ascii=False, indent=2))
    else:
        for ip in ips:
            print(ip)
    print(f"\n[*] 共 {len(ips)} 个 IP")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Proxy Pool: 自动收集、验证、保存并输出代理 IP"
    )
    parser.add_argument("--target", type=int, default=100, help="目标收集数量（默认 100）")
    parser.add_argument("--sources", default=None, help="指定源，逗号分隔")
    parser.add_argument("-o", "--output", default="proxy_pool.json", help="输出文件路径")
    parser.add_argument("-p", "--protocol", default="http", help="scdn 协议参数")
    parser.add_argument("--country-code", default=None, help="scdn 国家代码参数")
    parser.add_argument("-t", "--timeout", type=int, default=8, help="验证超时秒数")
    parser.add_argument("--no-verify", action="store_true", help="收集后跳过验证")
    parser.add_argument("--no-save", action="store_true", help="不保存到文件（仍会临时写入用于验证）")
    parser.add_argument("--json", action="store_true", help="以 JSON 数组格式输出")
    args = parser.parse_args(argv)

    # 1. 收集
    collect_ips(args.target, args.sources, args.output, args.protocol, args.country_code)

    # 2. 验证（可选）
    if not args.no_verify:
        verify_pool(args.output, args.timeout)

    # 3. 输出
    print("\n[*] 当前 IP 池：")
    output_pool(args.output, args.json)

    # 4. 清理（如果用户不想保存）
    if args.no_save and os.path.exists(args.output):
        os.remove(args.output)
        print(f"[*] 已清理临时文件: {args.output}")


if __name__ == "__main__":
    main()
