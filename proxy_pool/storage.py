"""代理存储模块：仅支持 JSON 格式。"""

import json
import os
from urllib.parse import urlparse


def extract_ip_port(proxy_url):
    """从代理 URL 中提取 host:port。"""
    try:
        parsed = urlparse(proxy_url)
        host = parsed.hostname
        port = parsed.port
        if host and port:
            return f"{host}:{port}"
    except Exception:
        pass

    try:
        core = proxy_url.split("//")[-1]
        if "@" in core:
            core = core.split("@")[-1]
        return core.strip("/")
    except Exception:
        return proxy_url


def load_ips(input_file):
    """从 JSON 文件读取 IP 列表。"""
    if not os.path.exists(input_file):
        return []

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    data = json.loads(content)
    return list(data.keys())
