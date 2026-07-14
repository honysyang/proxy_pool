#!/usr/bin/env python3
"""
收集 https://openclaw.allegro.earth/ 上暴露的 OpenClaw 实例 IP:端口。

用途：统计、安全研究、防御意识分析。
注意：这些不是代理服务器，不应作为代理使用。
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import requests

BASE_URL = "https://openclaw.allegro.earth"
DEFAULT_PORT = 18789


def fetch_page(page: int, timeout: int = 15):
    """获取指定页面并提取 IP:port 列表。"""
    url = f"{BASE_URL}/page/{page}/" if page > 1 else BASE_URL
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"请求 {url} 失败: {e}") from e

    html = resp.text
    ips = re.findall(r"[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}:[\d]+", html)

    # 去重并保持顺序
    seen = set()
    unique = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            unique.append(ip)

    # 解析总页数（只在第一页）
    total_pages = None
    if page == 1:
        m = re.search(r"Page:\s*\d+\s*/\s*(\d+)", html)
        if m:
            total_pages = int(m.group(1))

    return unique, total_pages


def collect(pages: int | None = None, delay: float = 1.0, output: str = "openclaw_stats.json"):
    """收集指定页数或全部页面的 IP。"""
    all_ips = []
    seen = set()

    # 先获取第一页，同时得到总页数
    print("[*] 正在获取第 1 页...")
    ips, total_pages = fetch_page(1)
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            all_ips.append(ip)
    print(f"    第 1 页: {len(ips)} 条，累计: {len(all_ips)} 条")

    if total_pages:
        print(f"[*] 站点总页数: {total_pages}")
        if pages is None or pages > total_pages:
            pages = total_pages

    if pages is None:
        pages = 1

    # 继续获取后续页面
    for page in range(2, pages + 1):
        time.sleep(delay)
        try:
            ips, _ = fetch_page(page)
        except Exception as e:
            print(f"[!] {e}", file=sys.stderr)
            continue
        for ip in ips:
            if ip not in seen:
                seen.add(ip)
                all_ips.append(ip)
        print(f"    第 {page} 页: {len(ips)} 条，累计: {len(all_ips)} 条", end="\r")

    print()  # 换行

    # 保存
    data = {
        "source": BASE_URL,
        "collected_at": datetime.now().isoformat(),
        "pages_fetched": pages,
        "total_ips": len(all_ips),
        "ips": all_ips,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[*] 完成: 共收集 {len(all_ips)} 条唯一 IP:端口")
    print(f"[*] 已保存到: {os.path.abspath(output)}")


def main():
    parser = argparse.ArgumentParser(
        description="收集 openclaw.allegro.earth 上暴露的 OpenClaw 实例 IP（仅用于统计/安全研究）"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="抓取页数，默认自动抓取全部",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="每页请求间隔秒数（默认 1.0，建议不要太快）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="openclaw_stats.json",
        help="输出文件路径（默认 openclaw_stats.json）",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="随机采样 N 条（在抓取完成后从结果中采样）",
    )
    args = parser.parse_args()

    collect(pages=args.pages, delay=args.delay, output=args.output)

    if args.sample:
        import random
        with open(args.output, "r", encoding="utf-8") as f:
            data = json.load(f)
        sample = random.sample(data["ips"], min(args.sample, len(data["ips"])))
        sample_output = args.output.replace(".json", "_sample.json")
        with open(sample_output, "w", encoding="utf-8") as f:
            json.dump({"sample_size": len(sample), "ips": sample}, f, ensure_ascii=False, indent=2)
        print(f"[*] 已采样 {len(sample)} 条保存到: {os.path.abspath(sample_output)}")


if __name__ == "__main__":
    main()
