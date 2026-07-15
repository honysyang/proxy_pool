"""Proxy Pool - 验证、存储、读取代理 IP。"""

__version__ = "0.1.0"

from .checker import check_proxy
from .storage import extract_ip_port, load_ips, save_ips

__all__ = [
    "check_proxy",
    "extract_ip_port",
    "load_ips",
    "save_ips",
]
