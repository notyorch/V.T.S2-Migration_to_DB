import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def get_database_url() -> URL:
    """Build a PostgreSQL connection URL from environment variables."""
    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    values = {key: os.getenv(key) for key in required_vars}
    missing = [key for key, value in values.items() if not value]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=values["DB_USER"],
        password=values["DB_PASSWORD"],
        host=values["DB_HOST"],
        port=int(values["DB_PORT"]),
        database=values["DB_NAME"],
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    artists_path = project_root / "data" / "artists.csv"
    tracks_path = project_root / "data" / "tracks.csv"

    try:
        engine = create_engine(get_database_url())

        artists_df = pd.read_csv(artists_path)
        tracks_df = pd.read_csv(tracks_path)

        artists_df.to_sql("artists", con=engine, if_exists="replace", index=False)
        tracks_df.to_sql("tracks", con=engine, if_exists="replace", index=False)

        print(f"artists: {len(artists_df)} registros insertados.")
        print(f"tracks: {len(tracks_df)} registros insertados.")
        print("Migracion completada correctamente.")
    except Exception as error:
        print(f"Error durante la migracion: {error}")
        raise


if __name__ == "__main__":
    main()
