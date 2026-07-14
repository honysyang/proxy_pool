"""IP 收集器：从多个代理源聚合指定数量的唯一 IP。

支持 API 提供商（Provider）和网页抓取器（Scraper）混合使用。
"""

import json
import os
from datetime import datetime

from .api import fetch_proxies
from .checker import build_proxy_dict
from .providers import list_providers
from .scrapers import get_scraper, list_scrapers
from .storage import extract_ip_port

DEFAULT_SOURCES = ["scdn"] + list(list_scrapers())


def collect_ips(
    target_count: int = 100,
    sources: list[str] | None = None,
    output_file: str = "proxy_pool.json",
    protocol: str = "http",
    api_count: int = 20,
    scrape_limit: int = 20,
    country_code: str | None = None,
) -> dict:
    """从多个源收集指定数量的唯一 IP 并合并到本地 JSON。

    Args:
        target_count: 目标收集数量
        sources: 源名称列表，如 ["scdn", "proxymist", "zdaye"]；默认全部
        output_file: 输出 JSON 文件
        protocol: API 提供商协议参数
        api_count: 每次 API 请求数量（1-20）
        scrape_limit: 每个网页源最多抓取数量
        country_code: API 国家代码参数

    Returns:
        dict: 统计信息
    """
    sources = sources or DEFAULT_SOURCES

    # 读取现有池
    existing = set()
    pool = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    pool = json.loads(content)
                    existing = set(pool.keys())
        except Exception:
            pass

    collected = []
    stats = {"sources": {}, "target": target_count}

    for source_name in sources:
        if len(collected) >= target_count:
            break

        source_stats = {"status": "ok", "count": 0}
        proxies = []

        try:
            if source_name in list_providers():
                # API provider
                raw = fetch_proxies(protocol=protocol, count=api_count, country_code=country_code, provider=source_name)
                for item in raw:
                    pd = build_proxy_dict(item, protocol)
                    if pd:
                        proxies.append(pd.get(list(pd.keys())[0]))
            elif source_name in list_scrapers():
                # Web scraper
                scraper = get_scraper(source_name)
                proxies = scraper.scrape(limit=scrape_limit)
            else:
                source_stats["status"] = "skipped"
                source_stats["error"] = "未知源"
                stats["sources"][source_name] = source_stats
                continue
        except Exception as e:
            source_stats["status"] = "error"
            source_stats["error"] = str(e)
            stats["sources"][source_name] = source_stats
            continue

        added_from_source = 0
        for proxy_url in proxies:
            ip_port = extract_ip_port(proxy_url)
            if not ip_port or ip_port in existing:
                continue

            protocol_name = proxy_url.split("://")[0] if "://" in proxy_url else protocol
            pool[ip_port] = {
                "protocol": protocol_name,
                "updated_at": datetime.now().isoformat(),
                "source": source_name,
            }
            existing.add(ip_port)
            collected.append(ip_port)
            added_from_source += 1

            if len(collected) >= target_count:
                break

        source_stats["count"] = added_from_source
        stats["sources"][source_name] = source_stats

    # 保存
    os.makedirs(os.path.dirname(os.path.abspath(output_file)) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    stats["collected"] = len(collected)
    stats["total"] = len(pool)
    return stats
