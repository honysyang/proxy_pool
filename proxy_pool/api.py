"""代理 API 统一入口。

通过 Provider 模式支持多代理源，默认使用 scdn。
"""

from .providers import get_provider, list_providers
from .providers.scdn import DEFAULT_API

__all__ = ["fetch_proxies", "DEFAULT_API", "list_providers"]


def fetch_proxies(api_url=DEFAULT_API, protocol="http", count=5, country_code=None, provider=None):
    """获取代理列表。

    Args:
        api_url: 保留参数，用于兼容旧接口；实际由 provider 决定
        protocol: 协议类型
        count: 获取数量
        country_code: 国家代码
        provider: 指定提供商名称，默认自动根据 api_url 推断

    Returns:
        list: 代理信息列表
    """
    name = provider or _guess_provider(api_url)
    p = get_provider(name)
    return p.fetch(protocol=protocol, count=count, country_code=country_code)


def _guess_provider(api_url: str) -> str:
    """根据 api_url 推断使用哪个提供商。"""
    if "scdn.io" in api_url:
        return "scdn"
    # 后续可扩展：根据 URL 特征匹配其他 provider
    return "scdn"
