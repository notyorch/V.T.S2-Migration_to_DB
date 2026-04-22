import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @classmethod
    def from_env(cls) -> "Settings":
        required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        values = {key: os.getenv(key) for key in required_vars}
        missing = [key for key, value in values.items() if not value]

        if missing:
            missing_csv = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {missing_csv}")

        return cls(
            db_host=values["DB_HOST"] or "",
            db_port=int(values["DB_PORT"] or 5432),
            db_name=values["DB_NAME"] or "",
            db_user=values["DB_USER"] or "",
            db_password=values["DB_PASSWORD"] or "",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
