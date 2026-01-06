"""
速率限制器配置

支持Cloudflare Tunnel和其他代理服务
"""
from slowapi import Limiter
from fastapi import Request


def get_real_ip(request: Request) -> str:
    """
    获取用户真实IP地址（支持Cloudflare Tunnel）

    Cloudflare会设置以下请求头：
    - CF-Connecting-IP: 用户真实IP (最可靠)
    - X-Forwarded-For: 代理链中的IP列表
    - X-Real-IP: 原始请求IP

    优先级:
    1. CF-Connecting-IP (Cloudflare专用，最可靠)
    2. X-Real-IP (Nginx/通用代理)
    3. X-Forwarded-For (标准代理头)
    4. request.client.host (直连)
    """
    # Cloudflare Tunnel / Cloudflare CDN
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip

    # Nginx或其他反向代理
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip

    # 标准代理头（取第一个IP）
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    # 直连（无代理）
    return request.client.host if request.client else "unknown"


# 初始化速率限制器，使用自定义IP获取函数
limiter = Limiter(key_func=get_real_ip)
