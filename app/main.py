from fastapi import FastAPI, HTTPException

from app.db import fetch_one

app = FastAPI(
    title="Spotify Data API",
    description="API base para servicio Python con FastAPI y PostgreSQL.",
    version="1.0.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Spotify Data API running"}


@app.get("/health")
def health() -> dict[str, str]:
    try:
        fetch_one("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database error: {error}") from error
