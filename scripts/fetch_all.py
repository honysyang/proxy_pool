#!/usr/bin/env python3
"""统一调度脚本：从 scripts/sources/ 下所有源收集 IP:端口并保存。"""

import argparse
import json
import os
import sys
from datetime import datetime

# 把项目根目录加入路径，方便 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sources import scdn, proxymist, zdaye, openclaw

SOURCES = {
    "scdn": scdn,
    "proxymist": proxymist,
    "zdaye": zdaye,
    "openclaw": openclaw,
}


def load_pool(path):
    """读取现有 JSON 池。"""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pool(path, pool):
    """保存 JSON 池。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def collect(target=100, sources=None, output="proxy_pool.json", protocol="http", country_code=None, fresh=False):
    """从指定源收集目标数量的新唯一 IP。"""
    sources = sources or list(SOURCES.keys())
    pool = {} if fresh else load_pool(output)
    existing = set(pool.keys())

    collected = 0
    stats = {}

    for name in sources:
        if name not in SOURCES:
            stats[name] = {"error": "未知源"}
            continue

        module = SOURCES[name]
        kwargs = {}
        if name == "scdn":
            kwargs = {"limit": 20, "protocol": protocol, "country_code": country_code}
        else:
            kwargs = {"limit": max(20, target // len(sources) + 10)}

        try:
            ips = module.fetch(**kwargs)
        except Exception as e:
            stats[name] = {"error": str(e), "count": 0}
            continue

        added = 0
        for ip in ips:
            if ":" not in ip:
                continue
            if ip in existing:
                continue
            pool[ip] = {
                "source": name,
                "updated_at": datetime.now().isoformat(),
            }
            existing.add(ip)
            collected += 1
            added += 1
            if collected >= target:
                break

        stats[name] = {"count": added}
        if collected >= target:
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
    parser = argparse.ArgumentParser(description="统一收集 IP:端口到本地 JSON 池")
    parser.add_argument("--target", type=int, default=100, help="目标收集数量（默认 100）")
    parser.add_argument("--sources", default=None, help=f"指定源，逗号分隔，默认全部: {list(SOURCES.keys())}")
    parser.add_argument("-o", "--output", default="proxy_pool.json", help="输出文件路径")
    parser.add_argument("-p", "--protocol", default="http", help="scdn 源协议参数")
    parser.add_argument("--country-code", default=None, help="scdn 源国家代码参数")
    parser.add_argument("--fresh", action="store_true", help="清空旧池子，重新收集")
    args = parser.parse_args()

    sources = args.sources.split(",") if args.sources else None
    result = collect(
        target=args.target,
        sources=sources,
        output=args.output,
        protocol=args.protocol,
        country_code=args.country_code,
        fresh=args.fresh,
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
