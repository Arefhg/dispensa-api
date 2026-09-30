from fastapi import FastAPI

from app.api.ingredients import router as ingredients_router
from app.errors import register_error_handlers

app = FastAPI(title="Dispensa API")
register_error_handlers(app)
app.include_router(ingredients_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
