"""storage 模块基础测试。"""

import json
import os
import tempfile

from proxy_pool.storage import extract_ip_port, load_ips, save_ips


def test_extract_ip_port():
    assert extract_ip_port("http://1.2.3.4:8080") == "1.2.3.4:8080"
    assert extract_ip_port("1.2.3.4:8080") == "1.2.3.4:8080"


def test_save_and_load_ips():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "pool.json")
        items = [
            {"proxy": "http://1.2.3.4:8080", "latency_ms": 100, "status": 200},
            {"proxy": "http://5.6.7.8:3128", "latency_ms": 150, "status": 200},
        ]
        save_ips(path, items, protocol="http", dedup=True, format="json")
        loaded = load_ips(path)
        assert set(loaded) == {"1.2.3.4:8080", "5.6.7.8:3128"}
