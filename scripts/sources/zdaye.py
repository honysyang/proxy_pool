"""从 zdaye.com 免费代理列表抓取。

注意：该站点有 WAF，可能不稳定。
"""

import re

import requests

URL = "https://www.zdaye.com/free/"


def _proxies(proxy):
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return {"http": proxy, "https": proxy}


def fetch(limit=20, proxy=None):
    """返回 ip:port 列表。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.zdaye.com/",
    }
    resp = requests.get(URL, headers=headers, proxies=_proxies(proxy), timeout=20)
    resp.raise_for_status()

    if resp.encoding in ("ISO-8859-1",):
        resp.encoding = resp.apparent_encoding or "gb2312"

    html = resp.text
    rows = re.findall(r'<ul class="ul-row">(.*?)</ul>', html, re.DOTALL)
    result = []
    for row in rows:
        ip = re.search(r'<p class="proxy_ip">([\d\.]+)</p>', row)
        port = re.search(r'<p class="proxy_port">Port：(\d+)', row)
        if ip and port:
            result.append(f"{ip.group(1)}:{port.group(1)}")
            if len(result) >= limit:
                break
    return result
