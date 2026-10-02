from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ingredients import router as ingredients_router
from app.api.suppliers import router as suppliers_router
from app.errors import register_error_handlers
from app.logging_config import configure_logging
from app.middleware import RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Called here, not at module import time: uvicorn configures its own
    # logging right before it starts serving, which would otherwise undo
    # whatever we set up earlier.
    configure_logging()
    yield


app = FastAPI(title="Dispensa API", lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
register_error_handlers(app)
app.include_router(ingredients_router)
app.include_router(suppliers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
