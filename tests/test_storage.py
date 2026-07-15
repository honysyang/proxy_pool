"""storage 模块基础测试。"""

import json
import os
import tempfile

from proxy_pool.storage import extract_ip_port, load_ips


def test_extract_ip_port():
    assert extract_ip_port("http://1.2.3.4:8080") == "1.2.3.4:8080"
    assert extract_ip_port("1.2.3.4:8080") == "1.2.3.4:8080"


def test_load_ips():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "pool.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "1.2.3.4:8080": {"protocol": "http"},
                "5.6.7.8:3128": {"protocol": "http"},
            }, f)
        loaded = load_ips(path)
        assert set(loaded) == {"1.2.3.4:8080", "5.6.7.8:3128"}
