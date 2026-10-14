"""
NEXORA Security Middleware — HTTP Headers & Defense-in-Depth Protections.
Applies secure response headers and prevents clickjacking, MIME-sniffing, and cross-site framing.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking / iframe embedding
        response.headers["X-Frame-Options"] = "DENY"

        # Cross-site scripting legacy filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser device hardware access
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Content Security Policy (allows CartoDB/OpenStreetMap tile layers and local API endpoints)
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        return response
