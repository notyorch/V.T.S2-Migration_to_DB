# Spotify Data API

<p>
  <img src="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Full_Logo_RGB_Green.png" alt="Spotify Logo" width="200" hspace="10">
  <img src="https://static.wixstatic.com/media/c6cbd8_e692ac3a7d78405fa0fa788bac52a1ad~mv2.png/v1/crop/x_0,y_337,w_3000,h_1426/fill/w_267,h_107,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/logotipo%20completo_color.png" alt="UPY Logo" width="200" hspace="10">
</p>

Python application using FastAPI and PostgreSQL in Docker.

This project simulates an external API server inside your local network (LAN) without exposing the service directly to the internet.

Made by:
* Jorge Enrique Vargas Pech | 2409244
* Jose Luis Rejón Quintal | 2409209
* William Emmanuel Fernández Castillo | 2409089
* Saúl Ruiz Peña | 2409218

***

## Architecture

- `api` (FastAPI): container `spotify_api`  
- `postgres` (PostgreSQL): container `spotify_db`  
- Internal Docker Compose network for service communication  
- API exposed on a specific LAN IP (`LAN_BIND_IP:8000`)  
- Database exposed on a specific LAN IP (`DB_BIND_IP:5432`) for external clients such as Power BI  

![Docker Compose Stack Running](/screenshots/docker-compose-ps.png)
(Containers `spotify_api`, `spotify_db`, `spotify_dashboard` in running/healthy state)

***

## Project Structure

```text
phase3/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── main.py
│   └── settings.py
├── data/
│   ├── artists.rar
│   └── tracks.rar
├── scripts/
│   └── load_csv_to_db.py
├── .dockerignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

![Project Structure](/screenshots/project-structure.png)

***

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Configure these values:

- `DB_HOST`  
- `DB_PORT`  
- `DB_NAME`  
- `DB_USER`  
- `DB_PASSWORD`  
- `LAN_BIND_IP`  
- `DB_BIND_IP`  

Suggested defaults:

- `DB_USER=yorch`  
- `DB_PASSWORD=Y0rch8mN2qLp7sTx`  

Important notes:

- When the API runs inside Docker Compose, `DB_HOST` should be the service name `postgres`.  
- When running scripts from the host to the Dockerized DB, use `DB_HOST=localhost`.  
- `LAN_BIND_IP` must be your actual LAN IP (e.g. `192.168.1.75`).  
- `DB_BIND_IP` must be your actual LAN IP when you want external clients (e.g. Power BI) to connect to PostgreSQL.

***

## Available Endpoints

Base URL (LAN):

- `http://<LAN_BIND_IP>:8000`

Endpoints:

1. `GET /` - basic API status message  
2. `GET /health` - database connectivity check  
3. `GET /kpis` - dashboard KPIs with optional filters by year and artist  
4. `GET /charts/trend-songs` - top 10 songs by median popularity  
5. `GET /charts/dance-vs-energy` - scatter plot dataset for danceability vs energy  
6. `GET /charts/popularity-over-time` - average popularity by year  
7. `GET /filters/artists` - artist list for the dashboard filter  
8. `GET /filters/year-range` - min/max release year for the dashboard filter  

Interactive documentation:

- Swagger: `http://<LAN_BIND_IP>:8000/docs`  
- ReDoc: `http://<LAN_BIND_IP>:8000/redoc`  

**Screenshot placeholders:**  
> `![Swagger UI - FastAPI docs](./images/swagger-docs.png)`  
> `![Sample /health response in Swagger](./images/swagger-health.png)`

***

## Option A: Run Everything with Docker Compose (recommended)

1. Start all services:

```bash
docker compose up -d --build
```

2. Check container status:

```bash
docker compose ps
```

3. Wait for automatic initialization:

```bash
docker compose logs -f api
```

On startup, the `api` container waits for PostgreSQL, extracts `artists.rar` and `tracks.rar` if needed, loads the data when the tables are missing, and then starts FastAPI automatically.

4. Test the API:

```bash
curl http://<LAN_BIND_IP>:8000/health
curl http://<LAN_BIND_IP>:8000/
```

5. Stop all services:

```bash
docker compose down
```

**Screenshot placeholder:**  
> `![api logs loading data on first boot](./images/api-bootstrap-logs.png)`

***

## Option B: DB in Docker, API on Host

1. Start only PostgreSQL:

```bash
docker compose up -d postgres
```

2. Set up local Python environment:

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

3. Confirm `.env` has `DB_HOST=localhost`.

4. Load CSV data into PostgreSQL:

```bash
python scripts/load_csv_to_db.py
```

5. Run the API exposed on the LAN:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

***

## Network Security (LAN, not Internet)

- The API is bound only to the IP specified by `LAN_BIND_IP`, not to all interfaces.  
- PostgreSQL is exposed on `DB_BIND_IP:5432` to allow access from the LAN (e.g. Power BI on another machine).  
- As long as you do not configure port forwarding on your router, the services are **not** exposed to the public internet.

***

## Connecting to the Streamlit Dashboard

1. Start the stack:

```bash
docker compose up -d --build
```

2. Open your browser at http://localhost:8501


3. Use the **Filtros** button (top-right) to filter by:
   - **Año de lanzamiento** — release year range
   - **Artistas** — search and select specific artists
   - **Muestra scatter** — sample size for the Danceability vs Energy chart (100–10,000 points)

4. Available charts:

   - **Top 10 canciones** — median popularity ranking for the selected period
   - **Danceability vs Energy** — scatter plot colored by popularity (random sample)
   - **Evolución de popularidad** — average popularity trend over time


> **Note:** `Artistas únicos` (98,504) counts distinct artists parsed from `public.tracks`, not the full `public.artists` catalog (1,104,349). This reflects artists with at least one song in the analyzed dataset.

![Spotify Analytics Dashboard](/screenshots/streamlit-dashboard.png)

Spotify Analytics — exploratory dashboard powered by Streamlit + FastAPI + PostgreSQL
***

## Connecting Power BI to PostgreSQL

1. Start the stack:

```bash
docker compose up -d --build
```

2. In Power BI Desktop, choose the **PostgreSQL database** connector.

3. Use these values:

- Server: `<DB_BIND_IP>:5432`  
- Database: `musicdb`  
- Username: `yorch`  
- Password: `Y0rch8mN2qLp7sTx`  

4. Load the `artists` and `tracks` tables.

5. If Power BI runs on another machine, open the firewall only for that specific IP on port `5432`.

![PowerBI PostgreSQL connection dialog](/screenshots/powerbi-connection.png)

PowerBI PostgreSQL connection dialog 

![PowerBI simple report using artists & tracks db](/screenshots/powerbi-report.png)
Simple PowerBI report using artists & tracks db
***




## Useful Commands

API logs:

```bash
docker compose logs -f api
```

Database logs:

```bash
docker compose logs -f postgres
```

Automatic bootstrap logs:

```bash
docker compose logs -f api
```

Recreate the stack:

```bash
docker compose down
docker compose up -d --build
```
