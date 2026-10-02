import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import request_id_var

logger = logging.getLogger("app.access")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _resolve_request_id(request: Request) -> str:
    incoming = request.headers.get("X-Request-ID")
    if incoming and _REQUEST_ID_RE.match(incoming):
        return incoming
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Gives every request a request_id and logs one access line for it.

    Never logs headers or the request body -- only method, path (no query
    string), status code and duration, so no secret (password, token,
    Authorization header) can end up in a log line.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _resolve_request_id(request)
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500
        try:
            try:
                response = await call_next(request)
            except Exception:
                logger.exception("unhandled error", extra={"request_id": request_id})
                raise
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )
            request_id_var.reset(token)
