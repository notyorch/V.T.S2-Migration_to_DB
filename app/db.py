from typing import Any
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def fetch_one(query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    engine = get_engine()
    with engine.connect() as connection:
        row = connection.execute(text(query), params or {}).mappings().first()
        return dict(row) if row else {}


def fetch_all(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    engine = get_engine()
    with engine.connect() as connection:
        rows = connection.execute(text(query), params or {}).mappings().all()
        return [dict(row) for row in rows]
