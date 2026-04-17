# Migracion CSV a base de datos relacional

Este proyecto migra datos desde archivos CSV hacia una base de datos PostgreSQL usando Python, pandas y SQLAlchemy.

## Proposito

El script toma los archivos `data/artists.csv` y `data/tracks.csv` y los carga en tablas PostgreSQL (`artists` y `tracks`).

## Como ejecutar la migracion

1. Instalar dependencias:

	```bash
	pip install -r requirements.txt
	```

2. Crear un archivo `.env` en la raiz del proyecto usando `.env.example` como base y completar los valores de conexion:

	- `DB_HOST`
	- `DB_PORT`
	- `DB_NAME`
	- `DB_USER`
	- `DB_PASSWORD`

3. Ejecutar el script de migracion:

	```bash
	python scripts/load_csv_to_db.py
	```

El proceso crea o reemplaza las tablas `artists` y `tracks` en la base de datos configurada e inserta todos los registros de ambos CSV.
