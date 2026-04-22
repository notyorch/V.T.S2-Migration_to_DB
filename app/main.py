from typing import Any

from fastapi import FastAPI, HTTPException, Query

from app.db import fetch_all, fetch_one

app = FastAPI(
    title="Spotify Data API",
    description="API base para servicio Python con FastAPI y PostgreSQL.",
    version="1.0.0",
)

YEAR_EXPR = """
CASE
    WHEN SUBSTRING(release_date FROM 1 FOR 4) ~ '^[0-9]{4}$'
    THEN SUBSTRING(release_date FROM 1 FOR 4)::int
    ELSE NULL
END
"""


def _table_exists(table_name: str) -> bool:
    query = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :table_name
    ) AS exists
    """
    row = fetch_one(query, {"table_name": table_name})
    return bool(row.get("exists", False))


def _build_track_filters(
    start_year: int | None,
    end_year: int | None,
    artists: list[str] | None,
) -> tuple[str, dict[str, Any]]:
    conditions: list[str] = []
    params: dict[str, Any] = {}

    if start_year is not None:
        conditions.append(f"{YEAR_EXPR} >= :start_year")
        params["start_year"] = start_year

    if end_year is not None:
        conditions.append(f"{YEAR_EXPR} <= :end_year")
        params["end_year"] = end_year

    valid_artists = [artist.strip() for artist in (artists or []) if artist and artist.strip()]
    if valid_artists:
        artist_conditions: list[str] = []
        for idx, artist_name in enumerate(valid_artists):
            param_name = f"artist_{idx}"
            artist_conditions.append(f"artists ILIKE :{param_name}")
            params[param_name] = f"%{artist_name}%"
        conditions.append(f"({' OR '.join(artist_conditions)})")

    where_sql = "WHERE " + " AND ".join(conditions) if conditions else ""
    return where_sql, params


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

# --- Endpoints para Dashboard ---

@app.get("/kpis")
def get_kpis(
    start_year: int | None = None,
    end_year: int | None = None,
    artists: list[str] | None = Query(default=None),
):
    try:
        if not _table_exists("artists") or not _table_exists("tracks"):
            return {
                "total_artists": 0,
                "total_tracks": 0,
                "avg_popularity": 0,
                "explicit_percentage": 0,
                "avg_duration_min": 0,
            }

        where_sql, params = _build_track_filters(start_year, end_year, artists)

        total_artists = fetch_one(
            f"""
            SELECT COUNT(DISTINCT artist_id) AS total
            FROM (
                SELECT
                    NULLIF(
                        BTRIM(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(split_part, '[', ''),
                                        ']', ''
                                    ),
                                    CHR(39), ''
                                ),
                                CHR(34), ''
                            )
                        ),
                        ''
                    ) AS artist_id
                FROM public.tracks
                CROSS JOIN LATERAL regexp_split_to_table(COALESCE(id_artists, ''), ',') AS split_part
                {where_sql}
            ) parsed
            """,
            params,
        )["total"]

        avg_popularity = fetch_one(
            f"SELECT AVG(popularity) as avg_pop FROM public.tracks {where_sql}",
            params,
        )["avg_pop"]
        total_tracks = fetch_one(
            f"SELECT COUNT(*) as total_tracks FROM public.tracks {where_sql}",
            params,
        )["total_tracks"]
        explicit_pct = fetch_one(
            f"""
            SELECT (
                AVG(
                    CASE
                        WHEN LOWER(COALESCE(explicit::text, '0')) IN ('1', 'true', 't') THEN 1
                        ELSE 0
                    END
                ) * 100.0
            ) AS pct
            FROM public.tracks
            {where_sql}
            """,
            params,
        )["pct"]
        avg_duration = fetch_one(
            f"SELECT AVG(duration_ms) / 60000.0 as avg_dur FROM public.tracks {where_sql}",
            params,
        )["avg_dur"]
        
        return {
            "total_artists": total_artists,
            "total_tracks": total_tracks,
            "avg_popularity": round(avg_popularity, 2) if avg_popularity else 0,
            "explicit_percentage": round(explicit_pct, 2) if explicit_pct else 0,
            "avg_duration_min": round(avg_duration, 2) if avg_duration else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/charts/trend-songs")
def get_trend_songs(
    start_year: int | None = None,
    end_year: int | None = None,
    artists: list[str] | None = Query(default=None),
):
    query = f"""
    SELECT name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY popularity) as median_popularity
    FROM public.tracks
    {{where_sql}}
    GROUP BY name
    ORDER BY median_popularity DESC
    LIMIT 10
    """
    try:
        if not _table_exists("tracks"):
            return []
        where_sql, params = _build_track_filters(start_year, end_year, artists)
        return fetch_all(query.format(where_sql=where_sql), params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/charts/dance-vs-energy")
def get_dance_vs_energy(
    start_year: int | None = None,
    end_year: int | None = None,
    artists: list[str] | None = Query(default=None),
    sample_size: int = 5000,
):
    query = f"""
    SELECT name, danceability, energy, popularity
    FROM public.tracks
    {{where_sql}}
    LIMIT :sample_size
    """
    try:
        if not _table_exists("tracks"):
            return []
        where_sql, params = _build_track_filters(start_year, end_year, artists)
        params["sample_size"] = max(100, min(sample_size, 10000))
        return fetch_all(query.format(where_sql=where_sql), params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/charts/popularity-over-time")
def get_popularity_over_time(
    start_year: int | None = None,
    end_year: int | None = None,
    artists: list[str] | None = Query(default=None),
):
    query = f"""
    SELECT
        {YEAR_EXPR} AS year,
        AVG(popularity) AS avg_popularity,
        COUNT(*) AS track_count
    FROM public.tracks
    __WHERE_SQL__
    GROUP BY year
    HAVING {YEAR_EXPR} IS NOT NULL
    ORDER BY year
    """
    try:
        if not _table_exists("tracks"):
            return []
        where_sql, params = _build_track_filters(start_year, end_year, artists)
        final_query = query.replace("__WHERE_SQL__", where_sql)
        return fetch_all(final_query, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/filters/artists")
def get_artists(search: str | None = None):
    try:
        if not _table_exists("artists"):
            return []
        if search:
            return fetch_all(
                "SELECT DISTINCT name FROM public.artists WHERE name ILIKE :search ORDER BY name LIMIT 500",
                {"search": f"%{search.strip()}%"},
            )
        return fetch_all("SELECT DISTINCT name FROM public.artists ORDER BY name LIMIT 2000")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/filters/year-range")
def get_year_range():
    try:
        if not _table_exists("tracks"):
            return {"min_year": 2000, "max_year": 2021}

        row = fetch_one(
            f"""
            SELECT
                MIN({YEAR_EXPR}) AS min_year,
                MAX({YEAR_EXPR}) AS max_year
            FROM public.tracks
            """
        )
        return {
            "min_year": int(row.get("min_year") or 2000),
            "max_year": int(row.get("max_year") or 2021),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
