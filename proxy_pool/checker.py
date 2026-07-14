"""代理验证模块。

通过代理访问 https://www.baidu.com 验证可用性。
"""

import time

import requests

VERIFY_URLS = [
    "https://www.baidu.com",
    "http://www.baidu.com",
]

# protocol=all 时，默认用 http 尝试验证
DEFAULT_VERIFY_PROTOCOL = "http"


def build_proxy_dict(proxy_info, protocol):
    """把 API 返回的代理信息转成 requests 可用的 proxies 字典。

    Args:
        proxy_info: 字符串（如 "1.2.3.4:8080" 或 "http://1.2.3.4:8080"）或字典
        protocol: 请求协议；当为 "all" 时，使用默认验证协议 http

    Returns:
        dict: 如 {"http": "http://1.2.3.4:8080"}
    """
    verify_protocol = protocol if protocol != "all" else DEFAULT_VERIFY_PROTOCOL

    if isinstance(proxy_info, dict):
        host = proxy_info.get("ip") or proxy_info.get("host")
        port = proxy_info.get("port")
        user = proxy_info.get("username") or proxy_info.get("user")
        pwd = proxy_info.get("password") or proxy_info.get("pass")
    elif isinstance(proxy_info, str):
        if proxy_info.startswith(("http://", "https://", "socks4://", "socks5://")):
            return {verify_protocol: proxy_info}
        return {verify_protocol: f"{verify_protocol}://{proxy_info}"}
    else:
        return None

    if not host or not port:
        return None

    if user and pwd:
        proxy_url = f"{verify_protocol}://{user}:{pwd}@{host}:{port}"
    else:
        proxy_url = f"{verify_protocol}://{host}:{port}"

    return {verify_protocol: proxy_url}


def check_proxy(proxies, timeout=8):
    """通过代理访问百度验证代理是否可用。

    Args:
        proxies: requests 风格的 proxies 字典
        timeout: 超时秒数

    Returns:
        tuple: (proxies, latency_ms, status_code)，失败时 latency_ms 为 None
    """
    start = time.time()
    protocol = [k for k in proxies.keys() if k in ("http", "https", "socks4", "socks5")][0]
    proxy_url = proxies[protocol]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Proxy-IP": proxy_url.split("//")[-1].split(":")[0],
    }
    for url in VERIFY_URLS:
        try:
            resp = requests.get(
                url,
                proxies=proxies,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
            )
            resp.raise_for_status()
            latency = int((time.time() - start) * 1000)
            return proxies, latency, resp.status_code
        except Exception:
            continue
    return proxies, None, None
