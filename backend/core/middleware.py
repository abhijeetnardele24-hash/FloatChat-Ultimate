"""Request context and lightweight in-memory rate limiting middleware."""

from __future__ import annotations

import logging
import time
import uuid
from collections import deque
from contextvars import ContextVar
from threading import Lock
from typing import Deque, Dict, Iterable, Tuple

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_ctx.get()


class RequestContextRateLimitMiddleware(BaseHTTPMiddleware):
    """Adds request IDs and applies per-client sliding-window rate limiting."""

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        requests_per_window: int = 120,
        window_seconds: int = 60,
        exempt_paths: Iterable[str] | None = None,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.requests_per_window = max(1, int(requests_per_window))
        self.window_seconds = max(1, int(window_seconds))
        self.exempt_paths = {p.strip() for p in (exempt_paths or []) if p and p.strip()}
        self._events: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip() or "unknown"
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _check_rate_limit(self, key: str) -> Tuple[bool, int]:
        now = time.monotonic()
        window_start = now - self.window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= window_start:
                events.popleft()
            if len(events) >= self.requests_per_window:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry_after
            events.append(now)
            return True, 0

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        response = None

        try:
            if self.enabled and request.url.path not in self.exempt_paths:
                allowed, retry_after = self._check_rate_limit(self._client_key(request))
                if not allowed:
                    response = JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Rate limit exceeded. Please retry later.",
                            "request_id": request_id,
                            "retry_after_seconds": retry_after,
                        },
                    )
                    response.headers["Retry-After"] = str(retry_after)
                    response.headers["X-Request-ID"] = request_id
                    return response

            response = await call_next(request)
            return response
        finally:
            process_time_ms = round((time.perf_counter() - start) * 1000, 2)
            if response is not None:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            request_id_ctx.reset(token)
