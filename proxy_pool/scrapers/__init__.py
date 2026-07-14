"""网页代理源抓取器注册与分发。"""

from .base import BaseScraper
from .proxymist import ProxyMistScraper
from .zdaye import ZdayeScraper

_registry: dict[str, BaseScraper] = {}


def register_scraper(scraper: BaseScraper) -> None:
    """注册一个网页代理源抓取器。"""
    if not isinstance(scraper, BaseScraper):
        raise TypeError("scraper 必须继承 BaseScraper")
    _registry[scraper.name] = scraper


def get_scraper(name: str) -> BaseScraper:
    """按名称获取已注册的抓取器。"""
    if name not in _registry:
        raise ValueError(f"未知抓取器: {name}，可用: {list(_registry.keys())}")
    return _registry[name]


def list_scrapers() -> list[str]:
    """返回所有已注册抓取器名称。"""
    return list(_registry.keys())


# 注册内置抓取器
register_scraper(ProxyMistScraper())
register_scraper(ZdayeScraper())
