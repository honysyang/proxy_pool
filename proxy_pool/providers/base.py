"""代理提供商基类。

后续新增 IP 池接口时，继承 BaseProvider 并实现 fetch 方法即可。
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """代理提供商抽象基类。"""

    name: str = ""
    default_api_url: str = ""

    @abstractmethod
    def fetch(self, protocol: str = "http", count: int = 5, country_code: str | None = None) -> list:
        """获取代理列表。

        Args:
            protocol: 协议类型
            count: 获取数量
            country_code: 国家代码

        Returns:
            list: 代理信息列表，元素为字符串或字典
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
