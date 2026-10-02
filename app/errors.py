"""Domain exceptions and the standard error envelope (DESIGN.md §3).

Every error response looks like: {"error": {"code": "...", "message": "..."}}
Routers/services raise NotFoundError / ConflictError; FastAPI's own
RequestValidationError (bad input) is caught too, so every error path -- not
just these two -- renders in the same shape.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, message: str = "Not found") -> None:
        self.message = message
        super().__init__(message)


class ConflictError(Exception):
    def __init__(self, message: str = "Conflict") -> None:
        self.message = message
        super().__init__(message)


class UnauthorizedError(Exception):
    def __init__(self, message: str = "Unauthorized") -> None:
        self.message = message
        super().__init__(message)


def _error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content=_error_body("not_found", exc.message))

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content=_error_body("conflict", exc.message))

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=_error_body("unauthorized", exc.message),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message = "; ".join(
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()
        )
        return JSONResponse(status_code=422, content=_error_body("invalid_input", message))
