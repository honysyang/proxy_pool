"""验证通过代理池访问目标 URL 时，服务器看到的不是本机真实 IP。

用法示例：
    # 1. 使用默认目标 https://httpbin.org/ip，对比直连 IP 与池子代理 IP
    python3 demo/test_pool_hide_ip.py

    # 2. 指向自己部署的 echo_server（需是公网可访问地址）
    python3 demo/test_pool_hide_ip.py --target-url http://你的服务器:5000/ip

    # 3. 指定池子文件并多测几次
    python3 demo/test_pool_hide_ip.py --pool proxy_pool.json --count 5
"""

import argparse
import os
import sys

import requests

# 把项目根目录加入 PYTHONPATH，才能导入 proxy_pool 模块
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from proxy_pool.storage import get_random_proxy


def build_proxies(proxy_str):
    """把 ip:port 转成 requests 能用的 proxies 字典。"""
    if not proxy_str:
        return None
    if "://" not in proxy_str:
        proxy_str = f"http://{proxy_str}"
    return {"http": proxy_str, "https": proxy_str}


def fetch_ip(url, proxies, timeout=15):
    resp = requests.get(url, proxies=proxies, timeout=timeout)
    resp.raise_for_status()
    return resp.text.strip()


def main():
    parser = argparse.ArgumentParser(description="验证代理池是否隐藏了本机真实 IP")
    parser.add_argument("--pool", default="proxy_pool.json", help="代理池 JSON 文件路径")
    parser.add_argument("--target-url", default="https://httpbin.org/ip", help="会回显访问者 IP 的目标 URL")
    parser.add_argument("--count", type=int, default=3, help="使用池子代理测试的次数")
    parser.add_argument("--timeout", type=int, default=15, help="每次请求超时秒数")
    args = parser.parse_args()

    print(f"[*] 目标 URL: {args.target_url}")

    # 1. 先测一次直连，得到本机 IP
    try:
        direct_text = fetch_ip(args.target_url, None, args.timeout)
        print(f"[DIRECT] 不经过代理时服务器看到的 IP/响应:\n{direct_text}\n")
    except Exception as e:
        print(f"[DIRECT] 直连请求失败: {e}\n")

    # 2. 从池子中随机选代理测试
    for i in range(1, args.count + 1):
        proxy = get_random_proxy(args.pool)
        if not proxy:
            print(f"[{i}] 池子为空，跳过")
            continue

        proxies = build_proxies(proxy)
        try:
            text = fetch_ip(args.target_url, proxies, args.timeout)
            print(f"[{i}] 使用代理 {proxy:<25} -> 服务器看到:\n{text}")
        except requests.exceptions.ProxyError as e:
            print(f"[{i}] 使用代理 {proxy:<25} -> 代理连接失败: {e}")
        except requests.exceptions.Timeout:
            print(f"[{i}] 使用代理 {proxy:<25} -> 请求超时")
        except Exception as e:
            print(f"[{i}] 使用代理 {proxy:<25} -> 其他错误: {type(e).__name__}: {e}")
        print()

    print("[*] 完成。如果上面所有代理返回的 IP 都和 [DIRECT] 不同，说明本机真实 IP 已被隐藏。")


if __name__ == "__main__":
    main()
