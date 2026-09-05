from fastapi import FastAPI

app = FastAPI(
    title="SIH26067 Ocean Backend",
    version="0.1.0",
    description="Server-side ocean model and observation scientific services.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
