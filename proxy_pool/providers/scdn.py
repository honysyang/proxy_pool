"""proxy.scdn.io 代理提供商实现。"""

import requests

from .base import BaseProvider

DEFAULT_API = "https://proxy.scdn.io/api/get_proxy.php"
VALID_PROTOCOLS = ("http", "https", "socks4", "socks5", "all")
MAX_COUNT = 20


class ScdnProvider(BaseProvider):
    """proxy.scdn.io 代理源。"""

    name = "scdn"
    default_api_url = DEFAULT_API

    def fetch(self, protocol: str = "http", count: int = 5, country_code: str | None = None) -> list:
        if protocol not in VALID_PROTOCOLS:
            raise ValueError(f"不支持的 protocol: {protocol}，可选: {VALID_PROTOCOLS}")
        if not isinstance(count, int) or count < 1 or count > MAX_COUNT:
            raise ValueError(f"count 必须在 1-{MAX_COUNT} 之间")

        params = {"protocol": protocol, "count": count}
        if country_code:
            params["country_code"] = country_code

        try:
            resp = requests.get(DEFAULT_API, params=params, timeout=15)
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

        proxies = self._extract_proxy_list(data)
        if not proxies:
            raise RuntimeError(f"API 未返回代理: code={code}, message={message}")

        return proxies

    @staticmethod
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
                    return ScdnProvider._extract_proxy_list(value)
        return []
