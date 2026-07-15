"""统一 CLI 入口：收集、验证、刷新、输出代理 IP 池。"""

import argparse
import json
import os
import subprocess
import sys

from .checker import check_proxy
from .storage import load_ips

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH_ALL = os.path.join(BASE_DIR, "scripts", "fetch_all.py")


def collect_ips(target, sources, output, protocol, country_code, use_pool_proxy=False):
    """调用 scripts/fetch_all.py 收集 IP。"""
    cmd = ["python3", FETCH_ALL, "--target", str(target), "--output", output, "--protocol", protocol]
    if sources:
        cmd.extend(["--sources", sources])
    if country_code:
        cmd.extend(["--country-code", country_code])
    if use_pool_proxy:
        cmd.append("--use-pool-proxy")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] 收集失败: {result.stderr or result.stdout}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())


def verify_pool(output, timeout):
    """验证本地池中所有代理，移除无效 IP。返回有效 IP 列表。"""
    ips = load_ips(output)
    if not ips:
        print("[*] 池子为空，跳过验证")
        return []

    print(f"[*] 开始验证 {len(ips)} 个代理...")
    pool = {}
    working = []
    failed = 0
    for ip in ips:
        pd = {"http": f"http://{ip}"}
        _, latency, status = check_proxy(pd, timeout=timeout)
        if latency is not None:
            pool[ip] = {"latency_ms": latency, "status": status, "updated_at": datetime_now()}
            working.append(ip)
            print(f"[OK] {ip:<30} 延迟: {latency:>4}ms 状态码: {status}")
        else:
            failed += 1
            print(f"[FAIL] {ip}")

    save_json(output, pool)
    print(f"\n[*] 验证完成：{len(working)} 可用，{failed} 已移除")
    return working


def fresh_pool(output, timeout):
    """刷新池子：验证并移除无效 IP。"""
    print("[*] 开始刷新池子（验证并移除无效 IP）...")
    return verify_pool(output, timeout)


def output_ips(ips, json_format):
    """输出 IP 列表。"""
    if json_format:
        print(json.dumps(ips, ensure_ascii=False, indent=2))
    else:
        for ip in ips:
            print(ip)


def datetime_now():
    from datetime import datetime
    return datetime.now().isoformat()


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Proxy Pool: 收集、验证、刷新、输出代理 IP")
    parser.add_argument("--target", type=int, default=None, help="收集 N 个 IP 到池子（默认验证）")
    parser.add_argument("--sources", default=None, help="指定源，逗号分隔")
    parser.add_argument("-o", "--output", default="proxy_pool.json", help="池子文件路径")
    parser.add_argument("-p", "--protocol", default="http", help="scdn 协议参数")
    parser.add_argument("--country-code", default=None, help="scdn 国家代码参数")
    parser.add_argument("-t", "--timeout", type=int, default=8, help="验证超时秒数")
    parser.add_argument("--no-verify", action="store_true", help="target 收集后跳过验证")
    parser.add_argument("--use-pool-proxy", action="store_true", help="使用池子中的随机代理进行收集（失败会自动回退直连）")
    parser.add_argument("--fresh", action="store_true", help="验证现有池子，移除无效 IP")
    parser.add_argument("--output-count", type=int, default=None, help="从池子输出 N 个 IP，不够则直接收集补足（不验证）")
    parser.add_argument("--json", action="store_true", help="JSON 数组格式输出")
    args = parser.parse_args(argv)

    # 1. 刷新池子：验证并移除无效 IP
    if args.fresh:
        fresh_pool(args.output, args.timeout)

    # 2. 收集 target 个 IP 到池子
    # 默认行为：没有指定 target、没有 output-count、没有 fresh 时，收集 100 个
    target = args.target
    if target is None and args.output_count is None and not args.fresh:
        target = 100

    if target is not None and target > 0:
        collect_ips(target, args.sources, args.output, args.protocol, args.country_code, args.use_pool_proxy)
        if not args.no_verify:
            verify_pool(args.output, args.timeout)

    # 3. 输出指定数量 IP，不够则补足
    if args.output_count is not None:
        ips = load_ips(args.output)
        needed = args.output_count - len(ips)
        if needed > 0:
            print(f"[*] 池子中仅有 {len(ips)} 个 IP，需要再收集 {needed} 个补足...")
            collect_ips(needed, args.sources, args.output, args.protocol, args.country_code, args.use_pool_proxy)
            ips = load_ips(args.output)

        output_ips(ips[:args.output_count], args.json)
        print(f"\n[*] 共输出 {min(args.output_count, len(ips))} 个 IP")
    else:
        # 没有 output-count 时，默认输出池子全部
        ips = load_ips(args.output)
        if ips:
            print("\n[*] 当前 IP 池：")
            output_ips(ips, args.json)
            print(f"\n[*] 共 {len(ips)} 个 IP")


if __name__ == "__main__":
    main()
