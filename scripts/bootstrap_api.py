import time
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load_csv_to_db import get_database_url, load_data


def wait_for_database(max_attempts: int = 60, delay_seconds: int = 2) -> None:
    """Wait until PostgreSQL accepts connections."""
    engine = create_engine(get_database_url(), pool_pre_ping=True)

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("PostgreSQL disponible.")
            return
        except OperationalError:
            print(f"Esperando PostgreSQL... intento {attempt}/{max_attempts}")
            time.sleep(delay_seconds)

    raise RuntimeError("PostgreSQL no estuvo disponible a tiempo.")


def main() -> None:
    wait_for_database()
    load_data(force_reload=False)


if __name__ == "__main__":
    main()
