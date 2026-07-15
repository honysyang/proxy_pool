"""从 proxymist.com 免费代理列表抓取。"""

import re

import requests

URL = "https://proxymist.com/zh/"


def _proxies(proxy):
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return {"http": proxy, "https": proxy}


def fetch(limit=20, proxy=None):
    """返回 ip:port 列表。"""
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, proxies=_proxies(proxy), timeout=20)
    resp.raise_for_status()
    html = resp.text

    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    result = []
    for row in rows:
        ip = re.search(r'<td class="table-ip"><strong>([\d\.]+)</strong></td>', row)
        port = re.search(r"<td>(\d+)</td>", row)
        if ip and port:
            result.append(f"{ip.group(1)}:{port.group(1)}")
            if len(result) >= limit:
                break
    return result
