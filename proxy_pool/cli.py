"""命令行入口。"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api import DEFAULT_API, MAX_COUNT, VALID_PROTOCOLS, fetch_proxies
from .checker import build_proxy_dict, check_proxy
from .storage import save_ips

DEFAULT_TIMEOUT = 8


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Proxy Pool: 获取、验证代理并保存去重后的 IP"
    )
    parser.add_argument("--api", default=DEFAULT_API, help="代理 API 地址")
    parser.add_argument(
        "-p", "--protocol",
        default="http",
        choices=VALID_PROTOCOLS,
        help="代理协议类型（默认 http；all 表示任意协议）",
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=5,
        help=f"获取代理数量，1-{MAX_COUNT}（默认 5）",
    )
    parser.add_argument(
        "--country-code",
        default=None,
        help="ISO 3166-1 两位国家代码，如 CN、US",
    )
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT, help="验证超时时间（秒）")
    parser.add_argument("-w", "--workers", type=int, default=10, help="并发验证线程数")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出到控制台")
    parser.add_argument("-q", "--quick", action="store_true", help="快速模式：只输出获取到的代理，不验证可用性")
    parser.add_argument("-o", "--output", default=None, help="保存 IP 的文件路径（默认根据 format 自动选择）")
    parser.add_argument(
        "-f", "--format",
        default="json",
        choices=["txt", "json"],
        help="保存格式：json 字典（默认，自动去重），txt 每行一个 IP",
    )
    parser.add_argument("--save-all", action="store_true", help="保存所有获取到的 IP（默认只保存验证通过的）")
    parser.add_argument("--no-dedup", action="store_true", help="保存时不去重")
    parser.add_argument("--no-save", action="store_true", help="不保存到本地文件")
    args = parser.parse_args(argv)

    if not 1 <= args.count <= MAX_COUNT:
        print(f"[!] count 必须在 1-{MAX_COUNT} 之间", file=sys.stderr)
        sys.exit(1)

    output_file = args.output or ("proxy_pool.json" if args.format == "json" else "proxy_pool.txt")

    extra = f"，国家 {args.country_code}" if args.country_code else ""
    print(f"[*] 正在从 {args.api} 获取 {args.count} 个 {args.protocol} 代理{extra}...")
    try:
        raw_proxies = fetch_proxies(args.api, args.protocol, args.count, args.country_code)
    except (ValueError, RuntimeError) as e:
        print(f"[!] {e}", file=sys.stderr)
        sys.exit(1)

    if not raw_proxies:
        print("[!] 未获取到任何代理", file=sys.stderr)
        sys.exit(1)

    proxy_dicts = []
    for item in raw_proxies:
        pd = build_proxy_dict(item, args.protocol)
        if pd:
            proxy_dicts.append(pd)

    if not proxy_dicts:
        print("[!] 未解析出任何可用代理", file=sys.stderr)
        sys.exit(1)

    if args.quick:
        proxy_urls = [p.get(list(p.keys())[0]) for p in proxy_dicts if p]
        if args.json:
            print(json.dumps(proxy_urls, ensure_ascii=False, indent=2))
        else:
            for url in proxy_urls:
                print(url)
        if not args.no_save:
            saved = save_ips(output_file, proxy_urls, protocol=args.protocol, dedup=not args.no_dedup, format=args.format)
            print(f"\n[*] 已保存 {len(saved)} 个 IP 到: {os.path.abspath(output_file)}")
        return

    print(f"[*] 获取到 {len(proxy_dicts)} 个代理，开始并发验证...")

    working = []
    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_proxy = {executor.submit(check_proxy, p, args.timeout): p for p in proxy_dicts}
        for future in as_completed(future_to_proxy):
            proxies, latency, status = future.result()
            proxy_url = proxies.get(list(proxies.keys())[0])
            if latency is not None:
                working.append({"proxy": proxy_url, "latency_ms": latency, "status": status})
                if not args.json:
                    print(f"[OK] {proxy_url:<45} 延迟: {latency:>4}ms  状态码: {status}")
            else:
                failed.append(proxies)
                if not args.json:
                    print(f"[FAIL] {proxy_url}")

    if args.json:
        print(json.dumps(working, ensure_ascii=False, indent=2))

    print(f"\n[*] 验证完成：{len(working)}/{len(proxy_dicts)} 个代理可用")

    if not args.no_save:
        if args.save_all:
            save_source = [p.get(list(p.keys())[0]) for p in proxy_dicts if p]
        else:
            save_source = working
        saved = save_ips(output_file, save_source, protocol=args.protocol, dedup=not args.no_dedup, format=args.format)
        source_label = "全部" if args.save_all else "可用"
        print(f"\n[*] 已保存 {len(saved)} 个{source_label} IP（去重后）到: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    main()
