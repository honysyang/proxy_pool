"""一个本地测试 API，记录所有来访请求的 IP 与请求头。

用法：
    python3 demo/echo_server.py

然后可通过浏览器或 curl 访问：
    curl http://127.0.0.1:5000/ip
    curl http://127.0.0.1:5000/logs
    curl -X POST http://127.0.0.1:5000/clear

注意：
- 若要让外网代理能访问到该 API，需要把服务部署到公网服务器，
  或使用 ngrok/frp 等工具把 127.0.0.1:5000 暴露到公网。
- 在同一台机器上直接访问，服务器看到的永远是 127.0.0.1，
  无法验证是否隐藏了真实公网 IP。
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_LOG = Path(__file__).with_name("access_log.jsonl")
LOG_LOCK = threading.Lock()


def _client_ip():
    # 优先取反向代理透传的 IP；否则取 TCP 连接远端 IP
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr


def _record():
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "ip": _client_ip(),
        "x_forwarded_for": request.headers.get("X-Forwarded-For", ""),
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
        "args": dict(request.args),
    }
    with LOG_LOCK:
        with open(ACCESS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@app.before_request
def before_request():
    _record()


@app.route("/")
def index():
    return jsonify({
        "msg": "这是测试 API，访问 /ip 可查看服务器记录的你的 IP，/logs 查看访问日志",
        "endpoints": ["/ip", "/logs", "/clear"],
    })


@app.route("/ip")
def ip():
    return jsonify({
        "ip": _client_ip(),
        "x_forwarded_for": request.headers.get("X-Forwarded-For", ""),
        "user_agent": request.headers.get("User-Agent", ""),
    })


@app.route("/logs")
def logs():
    if not ACCESS_LOG.exists():
        return jsonify([])
    with LOG_LOCK:
        lines = ACCESS_LOG.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return jsonify(records[-200:])  # 只返回最近 200 条


@app.route("/clear", methods=["POST", "GET"])
def clear():
    with LOG_LOCK:
        if ACCESS_LOG.exists():
            ACCESS_LOG.write_text("", encoding="utf-8")
    return jsonify({"msg": "日志已清空"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"[*] 测试 API 启动: http://127.0.0.1:{port}/")
    print(f"[*] 访问日志保存到: {ACCESS_LOG}")
    # debug=False，避免多线程日志写入冲突
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
