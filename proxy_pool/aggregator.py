"""代理聚合器：从多个网页源抓取并合并到本地 JSON 池。"""

import json
import os
from datetime import datetime

from .scrapers import BaseScraper, get_scraper, list_scrapers
from .storage import extract_ip_port




def merge_into_pool(
    output_file: str,
    scrapers: list[BaseScraper] | None = None,
    limit_per_source: int = 20,
    verify: bool = False,
) -> dict:
    """从多个网页源抓取代理并合并到本地 JSON 池。

    Args:
        output_file: 本地 JSON 池文件路径
        scrapers: 抓取器列表，默认使用所有已注册抓取器
        limit_per_source: 每个源最多抓取数量
        verify: 是否验证代理可用性（默认不验证，仅抓取）

    Returns:
        dict: 合并统计信息
    """
    from .checker import check_proxy

    if scrapers is None:
        scrapers = [get_scraper(name) for name in list_scrapers()]

    # 读取现有池
    pool = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    pool = json.loads(content)
        except Exception:
            pool = {}

    stats = {"sources": {}, "added": 0, "updated": 0, "total": len(pool)}

    for scraper in scrapers:
        try:
            proxies = scraper.scrape(limit=limit_per_source)
        except Exception as e:
            stats["sources"][scraper.name] = {"status": "error", "error": str(e), "count": 0}
            continue

        added = 0
        updated = 0
        for proxy_url in proxies:
            ip_port = extract_ip_port(proxy_url)
            if not ip_port:
                continue

            entry = {
                "protocol": proxy_url.split("://")[0] if "://" in proxy_url else "http",
                "updated_at": datetime.now().isoformat(),
                "source": scraper.name,
            }

            if verify:
                from .checker import build_proxy_dict
                pd = build_proxy_dict(proxy_url, entry["protocol"])
                if pd:
                    _, latency, status = check_proxy(pd, timeout=8)
                    if latency is not None:
                        entry["latency_ms"] = latency
                        entry["status"] = status
                    else:
                        entry["status"] = "failed"

            if ip_port in pool:
                updated += 1
            else:
                added += 1

            # 合并时保留已有字段并更新
            existing = pool.get(ip_port, {})
            existing.update(entry)
            pool[ip_port] = existing

        stats["sources"][scraper.name] = {"status": "ok", "count": len(proxies), "added": added, "updated": updated}
        stats["added"] += added
        stats["updated"] += updated

    stats["total"] = len(pool)

    # 保存
    os.makedirs(os.path.dirname(os.path.abspath(output_file)) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    return stats
