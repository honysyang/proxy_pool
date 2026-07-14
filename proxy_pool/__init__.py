"""Proxy Pool - 获取、验证并管理代理 IP。"""

__version__ = "0.1.0"

from .api import fetch_proxies
from .checker import check_proxy, build_proxy_dict
from .storage import extract_ip_port, save_ips, load_ips

__all__ = [
    "fetch_proxies",
    "check_proxy",
    "build_proxy_dict",
    "extract_ip_port",
    "save_ips",
    "load_ips",
]
