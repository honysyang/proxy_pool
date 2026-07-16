#!/usr/bin/env python3
"""统一调度脚本：从 scripts/sources/ 下所有源并发收集 IP:端口并保存为 JSON。"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proxy_pool.storage import get_random_proxy
from scripts.sources import scdn, proxymist, zdaye, openclaw

SOURCES = {
    "scdn": scdn,
    "proxymist": proxymist,
    "zdaye": zdaye,
    "openclaw": openclaw,
}


def load_pool(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pool(path, pool):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def _build_kwargs(name, limit, protocol, country_code, proxy):
    if name == "scdn":
        return {"limit": limit, "protocol": protocol, "country_code": country_code, "proxy": proxy}
    return {"limit": limit, "proxy": proxy}


def _fetch_one(name, limit, protocol, country_code, output, use_pool_proxy):
    """单个源的抓取任务，返回 (name, ips, error)。"""
    module = SOURCES[name]

    proxy = None
    if use_pool_proxy:
        proxy = get_random_proxy(output)
        if proxy:
            print(f"[*] [{name}] 尝试使用池子代理: {proxy}")

    kwargs = _build_kwargs(name, limit, protocol, country_code, proxy)

    try:
        ips = module.fetch(**kwargs)
    except Exception as e:
        if proxy:
            print(f"[!] [{name}] 通过代理失败: {e}，尝试直接请求...")
            kwargs["proxy"] = None
            try:
                ips = module.fetch(**kwargs)
            except Exception as e2:
                return name, [], f"代理失败: {e}; 直连失败: {e2}"
        else:
            return name, [], str(e)

    return name, ips, None


def collect(target=100, sources=None, output="proxy_pool.json", protocol="http", country_code=None, use_pool_proxy=False, workers=4):
    sources = sources or list(SOURCES.keys())
    pool = load_pool(output)
    existing = set(pool.keys())
    lock = Lock()

    collected = 0
    stats = {name: {"count": 0} for name in sources}
    round_num = 0

    while collected < target:
        round_num += 1
        round_added = 0
        # 每个源本轮要抓的数量：按剩余缺口均分，并留一点余量
        remaining = target - collected
        per_source = max(20, remaining // len(sources) + 10)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_fetch_one, name, per_source, protocol, country_code, output, use_pool_proxy): name
                for name in sources
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    _, ips, error = future.result()
                except Exception as e:
                    error = str(e)
                    ips = []

                if error:
                    # 只记录第一次错误，后续轮次若成功会覆盖
                    stats[name]["error"] = error
                    continue

                added = 0
                for ip in ips:
                    if ":" not in ip:
                        continue
                    with lock:
                        if ip in existing:
                            continue
                        pool[ip] = {"source": name, "updated_at": datetime.now().isoformat()}
                        existing.add(ip)
                        collected += 1
                        added += 1
                        if collected >= target:
                            break

                stats[name]["count"] = stats[name].get("count", 0) + added
                stats[name].pop("error", None)
                round_added += added

        print(f"[*] 第 {round_num} 轮完成，本轮新增: {round_added}，累计新增: {collected}")

        # 如果一轮都没有新增，说明所有源都已耗尽或全部失败，避免空转
        if round_added == 0:
            print("[!] 本轮未收集到任何新 IP，提前结束")
            break

    save_pool(output, pool)

    return {
        "target": target,
        "collected": collected,
        "total": len(pool),
        "sources": stats,
        "output": os.path.abspath(output),
    }


def main():
    parser = argparse.ArgumentParser(description="统一收集 IP:端口到 JSON 池")
    parser.add_argument("--target", type=int, default=100, help="目标收集数量")
    parser.add_argument("--sources", default=None, help=f"指定源，逗号分隔，默认全部: {list(SOURCES.keys())}")
    parser.add_argument("-o", "--output", default="proxy_pool.json", help="输出文件路径")
    parser.add_argument("-p", "--protocol", default="http", help="scdn 源协议参数")
    parser.add_argument("--country-code", default=None, help="scdn 国家代码参数")
    parser.add_argument("--use-pool-proxy", action="store_true", help="使用池子中的随机代理进行收集")
    parser.add_argument("--workers", type=int, default=4, help="并发源数（默认 4，设为 1 则串行）")
    args = parser.parse_args()

    sources = args.sources.split(",") if args.sources else None
    result = collect(
        target=args.target,
        sources=sources,
        output=args.output,
        protocol=args.protocol,
        country_code=args.country_code,
        use_pool_proxy=args.use_pool_proxy,
        workers=args.workers,
    )

    print(f"[*] 目标: {result['target']}，本次新增: {result['collected']}，池子总计: {result['total']}")
    for name, s in result["sources"].items():
        if "error" in s:
            print(f"    [{name}] 失败: {s['error']}")
        else:
            print(f"    [{name}] 新增: {s['count']} 条")
    print(f"[*] 已保存到: {result['output']}")


if __name__ == "__main__":
    main()
