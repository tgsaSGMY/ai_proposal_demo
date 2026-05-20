"""Extract the public client IP from a FastAPI Request.

Trust-the-proxy model: the demo runs behind Nginx Proxy Manager on the
Dev VPS, which sets X-Forwarded-For. Spoofing the leftmost forwarded IP
is possible but acceptable for a casual-abuse limiter — this is not a
security boundary.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request


def get_client_ip(request: Request) -> Optional[str]:
    """Return the visitor's public IP, or None if it can't be determined.

    Priority: leftmost X-Forwarded-For → X-Real-IP → request.client.host.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip() or None

    if request.client and request.client.host:
        return request.client.host

    return None
