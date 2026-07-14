"""代理提供商注册与分发。

新增提供商步骤：
1. 在 proxy_pool/providers/ 下新建模块，继承 BaseProvider
2. 在本文件顶部导入并调用 register_provider(provider_instance)
"""

from .base import BaseProvider
from .scdn import ScdnProvider

_registry: dict[str, BaseProvider] = {}


def register_provider(provider: BaseProvider) -> None:
    """注册一个代理提供商。"""
    if not isinstance(provider, BaseProvider):
        raise TypeError("provider 必须继承 BaseProvider")
    _registry[provider.name] = provider


def get_provider(name: str) -> BaseProvider:
    """按名称获取已注册的提供商。"""
    if name not in _registry:
        raise ValueError(f"未知代理提供商: {name}，可用: {list(_registry.keys())}")
    return _registry[name]


def list_providers() -> list[str]:
    """返回所有已注册提供商名称。"""
    return list(_registry.keys())


# 注册内置提供商
register_provider(ScdnProvider())
