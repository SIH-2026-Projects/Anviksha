from fastapi import FastAPI

from ocean_backend.api.routes.comparison import router as comparison_router


app = FastAPI(
    title="ANVIKSHA",
    version="0.1.0",
    description="Server-side ocean model and observation scientific services.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(comparison_router)