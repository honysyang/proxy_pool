"""ProxyMist 免费代理列表抓取。"""

import re

import requests

from .base import BaseScraper


class ProxyMistScraper(BaseScraper):
    """https://proxymist.com/zh/"""

    name = "proxymist"
    url = "https://proxymist.com/zh/"

    def scrape(self, limit: int = 20) -> list[str]:
        try:
            resp = requests.get(self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"请求 {self.url} 失败: {e}") from e

        html = resp.text
        rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
        proxies = []
        for row in rows:
            ip_match = re.search(r'<td class="table-ip"><strong>([\d\.]+)</strong></td>', row)
            port_match = re.search(r"<td>(\d+)</td>", row)
            proto_match = re.search(r"<td>(HTTP|HTTPS|SOCKS4|SOCKS5)</td>", row)
            if ip_match and port_match:
                proto = proto_match.group(1).lower() if proto_match else "http"
                proxies.append(f"{proto}://{ip_match.group(1)}:{port_match.group(1)}")
                if len(proxies) >= limit:
                    break

        return proxies
