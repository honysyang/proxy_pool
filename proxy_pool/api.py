"""代理 API 调用模块。

API 文档: https://proxy.scdn.io/api_docs.php
"""

import requests

DEFAULT_API = "https://proxy.scdn.io/api/get_proxy.php"
VALID_PROTOCOLS = ("http", "https", "socks4", "socks5", "all")
MAX_COUNT = 20


def fetch_proxies(api_url=DEFAULT_API, protocol="http", count=5, country_code=None):
    """从代理 API 获取代理列表。

    Args:
        api_url: 代理 API 地址
        protocol: 协议类型，支持 http、https、socks4、socks5、all
        count: 获取数量，1-20
        country_code: ISO 3166-1 两位国家代码，如 CN、US；默认 all

    Returns:
        list: 代理信息列表（元素为 "ip:port" 字符串）

    Raises:
        ValueError: 参数不合法
        RuntimeError: API 调用失败或返回错误
    """
    if protocol not in VALID_PROTOCOLS:
        raise ValueError(f"不支持的 protocol: {protocol}，可选: {VALID_PROTOCOLS}")
    if not isinstance(count, int) or count < 1 or count > MAX_COUNT:
        raise ValueError(f"count 必须在 1-{MAX_COUNT} 之间")

    params = {"protocol": protocol, "count": count}
    if country_code:
        params["country_code"] = country_code

    try:
        resp = requests.get(api_url, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"请求代理 API 失败: {e}") from e

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"解析 API 响应失败: {e}") from e

    code = data.get("code")
    message = data.get("message", "unknown")
    if code != 200:
        raise RuntimeError(f"API 返回错误: code={code}, message={message}")

    proxies = _extract_proxy_list(data)
    if not proxies:
        raise RuntimeError(f"API 未返回代理: code={code}, message={message}")

    return proxies


def _extract_proxy_list(data):
    """从多种可能的 JSON 结构中抽取出代理列表。"""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    for key in ("data", "list", "proxies", "results", "items"):
        if key in data:
            value = data[key]
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return _extract_proxy_list(value)
    return []
