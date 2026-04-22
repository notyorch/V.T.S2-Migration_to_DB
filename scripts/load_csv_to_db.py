import os
from pathlib import Path
import subprocess

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
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


def ensure_csv_extracted(project_root: Path) -> None:
    """Extract CSVs from RAR files when they are not present yet."""
    data_dir = project_root / "data"
    archives = {
        "artists.csv": data_dir / "artists.rar",
        "tracks.csv": data_dir / "tracks.rar",
    }

    for csv_name, rar_path in archives.items():
        csv_path = data_dir / csv_name
        if csv_path.exists():
            continue
        subprocess.run(
            ["unrar-free", "x", "-o+", str(rar_path), str(data_dir)],
            check=True,
        )


def tables_loaded(engine) -> bool:
    """Return True when both source tables exist and contain rows."""
    inspector = inspect(engine)
    required_tables = {"artists", "tracks"}
    existing_tables = set(inspector.get_table_names(schema="public"))

    if not required_tables.issubset(existing_tables):
        return False

    with engine.connect() as connection:
        artists_count = connection.execute(text("SELECT COUNT(*) FROM public.artists")).scalar_one()
        tracks_count = connection.execute(text("SELECT COUNT(*) FROM public.tracks")).scalar_one()

    return artists_count > 0 and tracks_count > 0


def load_data(force_reload: bool = False) -> None:
    """Load artists and tracks CSVs into PostgreSQL."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    artists_path = project_root / "data" / "artists.csv"
    tracks_path = project_root / "data" / "tracks.csv"

    engine = create_engine(get_database_url())
    ensure_csv_extracted(project_root)

    if not force_reload and tables_loaded(engine):
        print("artists y tracks ya existen con datos. Se omite la recarga.")
        return

    artists_df = pd.read_csv(artists_path)
    tracks_df = pd.read_csv(tracks_path)

    artists_df.to_sql("artists", con=engine, if_exists="replace", index=False)
    tracks_df.to_sql("tracks", con=engine, if_exists="replace", index=False)

    print(f"artists: {len(artists_df)} registros insertados.")
    print(f"tracks: {len(tracks_df)} registros insertados.")
    print("Migracion completada correctamente.")


def main() -> None:
    try:
        force_reload = os.getenv("FORCE_RELOAD_DB", "0") == "1"
        load_data(force_reload=force_reload)
    except Exception as error:
        print(f"Error durante la migracion: {error}")
        raise


if __name__ == "__main__":
    main()
