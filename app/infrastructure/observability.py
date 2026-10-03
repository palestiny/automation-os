from __future__ import annotations

import json
import logging
import time
from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_MAX_REQUEST_ID_LENGTH = 128
_REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def _normalize_request_id(value: str | None) -> str:
    if value is None:
        return str(uuid4())

    candidate = value.strip()
    if not candidate or len(candidate) > _MAX_REQUEST_ID_LENGTH:
        return str(uuid4())

    if any(ord(char) < 33 or ord(char) > 126 for char in candidate):
        return str(uuid4())

    return candidate


class JsonLogFormatter(logging.Formatter):
    """Serialize operational log records without adding application payloads."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "event": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
        }
        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        return json.dumps(payload, separators=(",", ":"))


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Add bounded correlation and safe request completion logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _normalize_request_id(request.headers.get(_REQUEST_ID_HEADER))
        token = _REQUEST_ID.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - started) * 1000
            logging.getLogger("automation_os.request").info(
                "http.request.completed",
            )
            response.headers[_REQUEST_ID_HEADER] = request_id
            logging.getLogger("automation_os.request").debug(
                "http.request.duration_ms=%.3f status=%s method=%s path=%s",
                elapsed_ms,
                response.status_code,
                request.method,
                request.url.path,
            )
            return response
        finally:
            _REQUEST_ID.reset(token)
