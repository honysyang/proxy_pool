"""storage 模块基础测试。"""

import json
import os
import tempfile

from proxy_pool.storage import extract_ip_port, load_ips, save_ips


def test_extract_ip_port():
    assert extract_ip_port("http://1.2.3.4:8080") == "1.2.3.4:8080"
    assert extract_ip_port("http://user:pass@1.2.3.4:8080") == "1.2.3.4:8080"
    assert extract_ip_port("1.2.3.4:8080") == "1.2.3.4:8080"


def test_save_ips_json_dedup():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "pool.json")
        items = [
            {"proxy": "http://1.2.3.4:8080", "latency_ms": 100, "status": 200},
            {"proxy": "http://1.2.3.4:8080", "latency_ms": 200, "status": 200},
            {"proxy": "http://1.2.3.5:3128", "latency_ms": 150, "status": 200},
        ]
        saved = save_ips(path, items, protocol="http", dedup=True, format="json")
        assert len(saved) == 2
        with open(path) as f:
            data = json.load(f)
        assert "1.2.3.4:8080" in data
        assert "1.2.3.5:3128" in data


def test_save_ips_txt():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "pool.txt")
        items = ["http://1.2.3.4:8080", "http://1.2.3.4:8080", "http://1.2.3.5:3128"]
        saved = save_ips(path, items, dedup=True, format="txt")
        assert saved == ["1.2.3.4:8080", "1.2.3.5:3128"]


def test_load_ips():
    with tempfile.TemporaryDirectory() as tmp:
        txt_path = os.path.join(tmp, "pool.txt")
        with open(txt_path, "w") as f:
            f.write("1.2.3.4:8080\n1.2.3.5:3128\n")
        assert load_ips(txt_path) == ["1.2.3.4:8080", "1.2.3.5:3128"]

        json_path = os.path.join(tmp, "pool.json")
        with open(json_path, "w") as f:
            json.dump({"2.2.2.2:8080": {}, "3.3.3.3:3128": {}}, f)
        assert set(load_ips(json_path)) == {"2.2.2.2:8080", "3.3.3.3:3128"}
