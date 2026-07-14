"""站大爷免费代理列表抓取。

注意：该站点有 WAF/反爬，可能不稳定。
"""

import re

import requests

from .base import BaseScraper


class ZdayeScraper(BaseScraper):
    """https://www.zdaye.com/free/"""

    name = "zdaye"
    url = "https://www.zdaye.com/free/"

    def scrape(self, limit: int = 20) -> list[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.zdaye.com/",
        }
        try:
            resp = requests.get(self.url, headers=headers, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"请求 {self.url} 失败: {e}") from e

        # 尝试自动检测编码
        if resp.encoding in ("ISO-8859-1",):
            resp.encoding = resp.apparent_encoding or "gb2312"

        html = resp.text
        rows = re.findall(r'<ul class="ul-row">(.*?)</ul>', html, re.DOTALL)
        proxies = []
        for row in rows:
            ip_match = re.search(r'<p class="proxy_ip">([\d\.]+)</p>', row)
            port_match = re.search(r'<p class="proxy_port">Port：(\d+)', row)
            proto_match = re.search(r'(HTTP|HTTPS|SOCKS4|SOCKS5)', row, re.I)
            if ip_match and port_match:
                proto = proto_match.group(1).lower() if proto_match else "http"
                proxies.append(f"{proto}://{ip_match.group(1)}:{port_match.group(1)}")
                if len(proxies) >= limit:
                    break

        return proxies
