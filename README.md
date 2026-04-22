# Spotify Data API

Aplicacion Python con FastAPI y PostgreSQL en Docker.

El proyecto queda listo para simular un servidor externo dentro de tu red local (LAN), sin exponer el servicio a internet de forma directa.

## Arquitectura

- `api` (FastAPI): contenedor `spotify_api`
- `postgres` (PostgreSQL): contenedor `spotify_db`
- Red de Docker Compose interna para comunicación entre servicios
- API expuesta en IP LAN específica (`LAN_BIND_IP:8000`)
- Base de datos expuesta en IP LAN específica (`DB_BIND_IP:5432`) para clientes externos como Power BI

## Estructura del proyecto

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

## Variables de entorno

Crea `.env` a partir de `.env.example`.

```bash
cp .env.example .env
```

Configura estos valores:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `LAN_BIND_IP`
- `DB_BIND_IP`

Valores por defecto sugeridos:

- `DB_USER=yorch`
- `DB_PASSWORD=Y0rch8mN2qLp7sTx`

Notas importantes:

- Si la API corre dentro de Docker Compose, `DB_HOST` se resuelve al servicio `postgres`.
- Si corres scripts desde host hacia DB dockerizada, usa `DB_HOST=localhost`.
- `LAN_BIND_IP` debe ser la IP LAN real de tu equipo (ejemplo: `192.168.1.75`).
- `DB_BIND_IP` debe ser la IP LAN real de tu equipo cuando quieras conectar clientes externos a PostgreSQL.

## Endpoints disponibles

Base URL:

- LAN: `http://<LAN_BIND_IP>:8000`

Endpoints:

1. `GET /`
2. `GET /health`

Documentacion interactiva:

- Swagger: `http://<LAN_BIND_IP>:8000/docs`
- ReDoc: `http://<LAN_BIND_IP>:8000/redoc`

## Opcion A: Ejecutar todo con Docker Compose (recomendado)

1. Levantar servicios:

```bash
docker compose up -d --build
```

2. Verificar estado:

```bash
docker compose ps
```

3. Esperar la inicializacion de datos:

```bash
docker compose logs -f seed_db
```

`seed_db` descomprime `artists.rar` y `tracks.rar` automaticamente, luego ejecuta la carga en PostgreSQL.

4. Probar API:

```bash
curl http://<LAN_BIND_IP>:8000/health
curl http://<LAN_BIND_IP>:8000/
```

5. Detener servicios:

```bash
docker compose down
```

## Opcion B: DB en Docker y API en host

1. Levantar solo PostgreSQL:

```bash
docker compose up -d postgres
```

2. Entorno Python local:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Confirmar `.env` con `DB_HOST=localhost`.

4. Cargar CSV:

```bash
python scripts/load_csv_to_db.py
```

5. Ejecutar API expuesta en LAN:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Seguridad de red (LAN, no internet)

- La API se publica en la IP indicada por `LAN_BIND_IP`, no en todas las interfaces.
- PostgreSQL se publica en `DB_BIND_IP:5432` para permitir acceso desde la LAN (ejemplo: Power BI en otra maquina).
- Mientras no abras puertos en router (port forwarding), no queda expuesto a internet.

## Conectar Power BI a PostgreSQL

1. Levanta el stack:

```bash
docker compose up -d --build
```

2. En Power BI Desktop, usa el conector **PostgreSQL database**.

3. Configura estos valores:

- Server: `<DB_BIND_IP>:5432`
- Database: `musicdb`
- Username: `yorch`
- Password: `Y0rch8mN2qLp7sTx`

4. Carga las tablas `artists` y `tracks`.

5. Si Power BI esta en otra maquina, abre firewall solo para esa IP en el puerto 5432.

## Comandos utiles

Logs de API:

```bash
docker compose logs -f api
```

Logs de DB:

```bash
docker compose logs -f postgres
```

Logs de carga inicial:

```bash
docker compose logs -f seed_db
```

Recrear stack:

```bash
docker compose down
docker compose up -d --build
```
