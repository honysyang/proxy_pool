"""从 openclaw.allegro.earth 收集暴露实例 IP:端口。

仅用于统计/安全研究，不作为代理使用。
"""

import re
import time

import requests

BASE_URL = "https://openclaw.allegro.earth"


def _proxies(proxy):
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return {"http": proxy, "https": proxy}


def fetch(limit=100, delay=1.0, proxy=None):
    """返回 ip:port 列表，limit 为抓取页数 * 约 100。"""
    result = []
    seen = set()
    pages = max(1, (limit + 99) // 100)

    for page in range(1, pages + 1):
        url = f"{BASE_URL}/page/{page}/" if page > 1 else BASE_URL
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, proxies=_proxies(proxy), timeout=15)
        resp.raise_for_status()

        ips = re.findall(r"[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}:[\d]+", resp.text)
        for ip in ips:
            if ip not in seen:
                seen.add(ip)
                result.append(ip)

        if page < pages:
            time.sleep(delay)

    return result[:limit]
