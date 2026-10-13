"""Small ASGI boundary with generated request IDs and sanitized error responses."""

import logging
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("companyos.requests")


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {
            "code": code,
            "message": message,
            "details": [] if details is None else details,
            "request_id": request.state.request_id,
        }},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic errors can contain raw input and context; do not serialize them.
    return error_response(request, 422, "validation_error", "Request validation failed")


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    messages = {
        401: ("unauthenticated", "Authentication required"),
        403: ("forbidden", "Access forbidden"),
        404: ("not_found", "Resource not found"),
        405: ("method_not_allowed", "Method not allowed"),
    }
    code, message = messages.get(exc.status_code, ("request_error", "Request failed"))
    response = error_response(request, exc.status_code, code, message)
    if exc.status_code == 405 and exc.headers and "Allow" in exc.headers:
        response.headers["Allow"] = exc.headers["Allow"]
    return response


class RequestSafetyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = False

        async def safe_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = [
                    (key, value) for key, value in message.get("headers", [])
                    if key.lower() not in (b"x-request-id", b"cache-control")
                ]
                message = {**message, "headers": headers + [
                    (b"x-request-id", request_id.encode("ascii")),
                    (b"cache-control", b"private, no-store"),
                ]}
            await send(message)

        try:
            await self.app(scope, receive, safe_send)
        except Exception:
            # No exception text, stack, URL/query, headers, or body in this log.
            logger.error("Unhandled request failure; request_id=%s", request_id)
            if started:
                raise RuntimeError("Response failed after headers were sent") from None
            response = error_response(
                Request(scope), 500, "internal_error", "Unexpected server error"
            )
            await response(scope, receive, safe_send)
