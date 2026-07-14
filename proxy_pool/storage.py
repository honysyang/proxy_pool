"""代理存储模块：支持 txt / json 格式、自动去重。"""

import json
import os
from datetime import datetime
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


def _item_to_proxy_url(item):
    """统一把字符串或字典转成 (proxy_url, meta_dict)。"""
    if isinstance(item, str):
        return item, {}
    if isinstance(item, dict):
        return item.get("proxy"), item
    return None, {}


def save_ips(output_file, proxy_items, protocol="http", dedup=True, format="json"):
    """保存代理到文件。

    Args:
        output_file: 输出文件路径
        proxy_items: 字符串列表或包含 proxy 字段的字典列表
        protocol: 协议类型，写入元数据
        dedup: 是否去重
        format: "txt" 或 "json"

    Returns:
        list: 实际保存的 IP:port 列表
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_file)) or ".", exist_ok=True)

    if format == "json":
        return _save_ips_json(output_file, proxy_items, protocol, dedup)

    lines = []
    seen = set()
    for item in proxy_items:
        proxy_url, _ = _item_to_proxy_url(item)
        if not proxy_url:
            continue
        ip_port = extract_ip_port(proxy_url)
        if not ip_port:
            continue
        if dedup and ip_port in seen:
            continue
        if dedup:
            seen.add(ip_port)
        lines.append(ip_port)

    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")
    return lines


def _save_ips_json(output_file, proxy_items, protocol, dedup):
    """以 JSON 字典格式保存：{ "ip:port": { meta } }，键自然去重。"""
    result = {}
    for item in proxy_items:
        proxy_url, meta = _item_to_proxy_url(item)
        if not proxy_url:
            continue
        ip_port = extract_ip_port(proxy_url)
        if not ip_port:
            continue

        entry = {
            "protocol": protocol,
            "updated_at": datetime.now().isoformat(),
        }
        if "latency_ms" in meta:
            entry["latency_ms"] = meta["latency_ms"]
        if "status" in meta:
            entry["status"] = meta["status"]

        if not dedup and ip_port in result:
            entry["occurrences"] = result[ip_port].get("occurrences", 1) + 1
        result[ip_port] = entry

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return list(result.keys())


def load_ips(input_file):
    """从文件读取代理列表，支持 txt 与 json 格式。

    Returns:
        list: IP:port 字符串列表
    """
    if not os.path.exists(input_file):
        return []

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    if content.startswith("{"):
        data = json.loads(content)
        return list(data.keys())

    return [line.strip() for line in content.splitlines() if line.strip()]
