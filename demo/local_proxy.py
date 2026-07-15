"""一个最小化的本地 HTTP/HTTPS 正向代理，用于在私有网络内验证代理转发。

用法：
    python3 demo/local_proxy.py [--port 8080]

然后把它加入池子（例如手动创建 demo/local_pool.json）：
    echo '{"127.0.0.1:8080": {}}' > demo/local_pool.json

再用验证脚本访问私有网络目标：
    python3 demo/test_pool_hide_ip.py \
        --pool demo/local_pool.json \
        --target-url http://192.168.56.103:5000/ip \
        --count 3

注意：
- 这个代理运行在本地，所以目标服务器看到的仍然是本机 IP；
  要真正“隐藏 IP”，需要把代理部署到另一台能访问目标网络的机器上。
- 该代理仅用于验证“请求确实走了代理”以及“代理能访问私网目标”。
"""

import argparse
import select
import socket
import socketserver
import threading
from urllib.parse import urlparse


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class ProxyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        try:
            first_line = conn.recv(4096)
        except OSError:
            return
        if not first_line:
            return

        # CONNECT 方法用于 HTTPS 隧道
        if first_line.startswith(b"CONNECT "):
            self._handle_connect(conn, first_line)
        else:
            self._handle_http(conn, first_line)

    def _parse_connect(self, first_line):
        # CONNECT host:port HTTP/1.1
        parts = first_line.split()
        if len(parts) < 2:
            return None, None
        host_port = parts[1].decode("utf-8", "ignore")
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            return host, int(port)
        return host_port, 443

    def _handle_connect(self, client, first_line):
        host, port = self._parse_connect(first_line)
        if not host:
            client.close()
            return

        try:
            remote = socket.create_connection((host, port), timeout=20)
        except OSError as e:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            client.close()
            print(f"[!] CONNECT {host}:{port} 失败: {e}")
            return

        client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        self._relay(client, remote)

    def _handle_http(self, client, first_line):
        # 解析请求头，找到 Host
        header_data = first_line
        while b"\r\n\r\n" not in header_data:
            chunk = client.recv(4096)
            if not chunk:
                client.close()
                return
            header_data += chunk

        try:
            header_text = header_data.decode("utf-8", "ignore")
            lines = header_text.split("\r\n")
            req_line = lines[0]
            method, url, version = req_line.split(" ", 2)
        except Exception as e:
            client.close()
            print(f"[!] 解析 HTTP 请求失败: {e}")
            return

        # 如果 URL 是绝对路径，提取目标
        if url.startswith("http://"):
            parsed = urlparse(url)
            target_host = parsed.hostname
            target_port = parsed.port or 80
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
        else:
            # 相对路径，从 Host 头取
            host_header = ""
            for line in lines[1:]:
                if line.lower().startswith("host:"):
                    host_header = line.split(":", 1)[1].strip()
                    break
            if not host_header:
                client.close()
                return
            if ":" in host_header:
                target_host, target_port = host_header.rsplit(":", 1)
                target_port = int(target_port)
            else:
                target_host = host_header
                target_port = 80
            path = url

        # 重建请求行
        new_req_line = f"{method} {path} {version}\r\n"
        # 去掉 hop-by-hop 头和 Proxy-Connection
        skip_headers = {
            "proxy-connection", "connection", "keep-alive", "transfer-encoding",
            "upgrade", "proxy-authorization",
        }
        new_headers = []
        for line in lines[1:]:
            if not line:
                continue
            if ":" in line:
                key = line.split(":", 1)[0].strip().lower()
                if key in skip_headers:
                    continue
            new_headers.append(line)

        new_request = (new_req_line + "\r\n".join(new_headers) + "\r\n\r\n").encode("utf-8")

        try:
            remote = socket.create_connection((target_host, target_port), timeout=20)
        except OSError as e:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            client.close()
            print(f"[!] 连接目标 {target_host}:{target_port} 失败: {e}")
            return

        remote.sendall(new_request)

        # 继续转发剩余请求体（如果有 Content-Length）
        content_length = 0
        for line in lines[1:]:
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break
        body_received = len(header_data) - header_data.find(b"\r\n\r\n") - 4
        remaining = content_length - body_received
        if remaining > 0:
            while remaining > 0:
                chunk = client.recv(min(4096, remaining))
                if not chunk:
                    break
                remote.sendall(chunk)
                remaining -= len(chunk)

        self._relay(client, remote)

    def _relay(self, client, remote):
        try:
            while True:
                readable, _, _ = select.select([client, remote], [], [], 60)
                if not readable:
                    break
                if client in readable:
                    data = client.recv(4096)
                    if not data:
                        break
                    remote.sendall(data)
                if remote in readable:
                    data = remote.recv(4096)
                    if not data:
                        break
                    client.sendall(data)
        except OSError:
            pass
        finally:
            client.close()
            remote.close()


def main():
    parser = argparse.ArgumentParser(description="本地最小化正向代理")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, args.port), ProxyHandler)
    print(f"[*] 本地代理已启动: {args.host}:{args.port}")
    print("[*] 按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 停止代理")
        server.shutdown()


if __name__ == "__main__":
    main()
