"""
NEXORA Rate Limiting & Abuse Prevention Core.
Implements in-memory sliding-window request throttling for security-sensitive endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

from app.core.config import settings

# Thread-safe in-memory store for tracking request timestamps: {key: [timestamp1, timestamp2, ...]}
_login_attempts: Dict[str, List[float]] = defaultdict(list)


def check_login_rate_limit(request: Request, username: str = ""):
    """
    Enforces sliding-window rate limits on login attempts based on client IP and target username.
    Prevents automated credential brute-forcing and dictionary attacks.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{username.strip().lower()}"
    now = time.time()
    window = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
    max_attempts = settings.RATE_LIMIT_LOGIN_MAX

    # Purge expired timestamps older than sliding window
    attempts = [t for t in _login_attempts[key] if now - t < window]
    _login_attempts[key] = attempts

    if len(attempts) >= max_attempts:
        retry_after = int(window - (now - attempts[0])) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Throttled. Try again in {max_attempts} seconds.",
            headers={"Retry-After": str(max(1, retry_after))}
        )

    # Record this attempt
    _login_attempts[key].append(now)


def reset_rate_limit(request: Request, username: str = ""):
    """Clears rate limit record upon successful authentication."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{username.strip().lower()}"
    if key in _login_attempts:
        del _login_attempts[key]
