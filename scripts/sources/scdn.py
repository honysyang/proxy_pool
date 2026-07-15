"""从 proxy.scdn.io API 获取代理。"""

import requests

URL = "https://proxy.scdn.io/api/get_proxy.php"


def _proxies(proxy):
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return {"http": proxy, "https": proxy}


def fetch(limit=20, protocol="http", country_code=None, proxy=None):
    """返回 ip:port 列表。"""
    params = {"protocol": protocol, "count": min(limit, 20)}
    if country_code:
        params["country_code"] = country_code

    resp = requests.get(URL, params=params, proxies=_proxies(proxy), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 200:
        raise RuntimeError(f"API error: {data}")

    proxies = data.get("data", {}).get("proxies", [])
    return [p for p in proxies if ":" in p]
