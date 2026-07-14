"""网页代理源抓取基类。

用于从免费代理列表网站直接爬取 IP:port。
"""

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """网页代理源抓取器抽象基类。"""

    name: str = ""
    url: str = ""

    @abstractmethod
    def scrape(self, limit: int = 20) -> list[str]:
        """抓取代理列表。

        Args:
            limit: 最多返回数量

        Returns:
            list: 代理 URL 列表，如 ["http://1.2.3.4:8080", ...]
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
