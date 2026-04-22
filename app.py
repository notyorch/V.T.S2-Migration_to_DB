import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import os

# Configuración de la página
st.set_page_config(
    page_title="Spotify Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

spotify_template = go.layout.Template()
spotify_template.layout = go.Layout(
    paper_bgcolor="#000000",
    plot_bgcolor="#000000",
    font=dict(color="#FFFFFF", family="Cabinet Grotesk, Inter, sans-serif"),
    colorway=["#1DB954", "#1ed760", "#B3B3B3", "#535353"],
    hoverlabel=dict(
        bgcolor="#121212",
        bordercolor="#1DB954",
        font=dict(color="white", size=13),
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
)
pio.templates["spotify"] = spotify_template
pio.templates.default = "spotify"

# --- ESTILO SPOTIFY (Dark Mode + Neon Green) ---
st.markdown("""
    <style>
    @import url('https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@700,800,400&display=swap');

    html, body, [class*="css"] {
        background-color: #000000 !important;
    }
    .stApp {
        background: #000000;
    }
    /* Aplicar fuente solo a texto, NUNCA a elementos que usan iconos */
    body, p, span:not(.material-icons):not(.material-symbols-outlined):not(.material-symbols-rounded),
    div:not([data-testid="stIconMaterial"]), label, h1, h2, h3, h4 {
        font-family: 'Cabinet Grotesk', 'Inter', sans-serif;
    }
    /* Preservar explícitamente la fuente de íconos de Material */
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined,
    [data-testid="stIconMaterial"] {
        font-family: 'Material Icons' !important;
    }
    [data-testid="stPopoverButton"] .material-icons,
    [data-testid="stPopoverButton"] .material-symbols-rounded,
    [data-testid="stPopoverButton"] .material-symbols-outlined,
    [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
        display: none !important;
    }
    h1, h2, h3, h4, [data-testid="stMetricLabel"] {
        font-family: 'Cabinet Grotesk', Inter, sans-serif;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
    }
    h3 a { display: none; }

    /* KPI cards — Spotify 2024 */
    [data-testid="metric-container"] {
        background: #121212;
        border-radius: 8px;
        padding: 1.25rem;
        border: none;
        box-shadow: none;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    [data-testid="stMetricLabel"] {
        color: #B3B3B3;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px;
    }
    [data-baseweb="popover"] {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN API ---
# En Docker, usar API_BASE_URL=http://api:8000. En host local, por defecto localhost.
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = 30


@st.cache_data(ttl=600)
def _fetch_data_cached(endpoint: str, params_tuple: tuple[tuple[str, str], ...]):
    params = dict(params_tuple)
    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def fetch_data(endpoint, params=None):
    params = params or {}
    if isinstance(params, dict):
        flat_params: list[tuple[str, str]] = []
        for key, value in params.items():
            if isinstance(value, list):
                for item in value:
                    flat_params.append((str(key), str(item)))
            else:
                flat_params.append((str(key), str(value)))
    else:
        flat_params = [(str(k), str(v)) for k, v in params]

    params_tuple = tuple(sorted(flat_params))
    try:
        data = _fetch_data_cached(endpoint, params_tuple)
        return data, None
    except requests.exceptions.Timeout:
        return None, "La API tardó demasiado en responder."
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con la API."
    except requests.exceptions.RequestException:
        return None, "Ocurrió un error consultando la API."


def show_retry(section_key: str):
    if st.button("Reintentar", key=f"retry_{section_key}"):
        _fetch_data_cached.clear()
        st.rerun()


def fetch_section(section_key: str, endpoint: str, params=None, loading_text="Cargando datos"):
    with st.spinner(loading_text):
        data, error = fetch_data(endpoint, params)
    if error:
        st.error(f"No se pudo cargar {section_key.lower()}. {error}")
        show_retry(section_key)
        return None
    return data


def format_delta(current_value: float, previous_value: float | None, suffix: str = "") -> str | None:
    if previous_value is None or previous_value == 0:
        return None
    delta_pct = ((current_value - previous_value) / previous_value) * 100
    return f"{delta_pct:+.1f}%{suffix}"


def format_thousands(value: int | float) -> str:
    return f"{int(value):,}"

# --- HEADER + FILTROS ---
col_brand, col_filters = st.columns([3, 1])

with col_brand:
    st.image(
        "https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Full_Logo_RGB_White.png",
        width=280,
    )
    st.caption("Fuente: [Spotify Dataset — Kaggle](https://www.kaggle.com/datasets/nimishasen27/spotify-dataset)")

year_meta = fetch_section("Años", "/filters/year-range", loading_text="Cargando rango de años")
min_year = int((year_meta or {}).get("min_year", 2000))
max_year = int((year_meta or {}).get("max_year", 2021))

with col_filters:
    with st.popover("Filtros", use_container_width=True):
        year_range = st.slider(
            "Año de lanzamiento",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
        )
        year_min, year_max = year_range
        artist_search = st.text_input("Buscar artista", value="")
        artist_query_params = {"search": artist_search} if artist_search else None
        artists_data = fetch_section(
            "Artistas",
            "/filters/artists",
            params=artist_query_params,
            loading_text="Cargando artistas",
        )
        artist_options = [a["name"] for a in artists_data] if artists_data else []
        selected_artists = st.multiselect("Seleccionar artistas", artist_options)
        scatter_sample = st.slider("Muestra scatter", 100, 10000, 5000, step=100)

st.caption("Análisis exploratorio del catálogo de Spotify · Datos hasta 2021")

query_params = {
    "start_year": year_range[0],
    "end_year": year_range[1],
}
if selected_artists:
    query_params["artists"] = selected_artists

span_years = year_range[1] - year_range[0]
prev_end = year_range[0] - 1
previous_params = None
if prev_end >= min_year:
    previous_params = {
        "start_year": max(min_year, prev_end - span_years),
        "end_year": prev_end,
    }
    if selected_artists:
        previous_params["artists"] = selected_artists

# --- KPIs (FILA SUPERIOR) ---
kpis = fetch_section("KPIs", "/kpis", params=query_params, loading_text="Calculando KPIs")
previous_kpis = None
if previous_params:
    previous_kpis = fetch_section("KPIs previos", "/kpis", params=previous_params, loading_text="Calculando comparativo")

if kpis:
    col1, col2, col3, col4 = st.columns(4)

    prev_total = previous_kpis["total_artists"] if previous_kpis else None
    prev_pop = previous_kpis["avg_popularity"] if previous_kpis else None
    prev_exp = previous_kpis["explicit_percentage"] if previous_kpis else None
    prev_dur = previous_kpis["avg_duration_min"] if previous_kpis else None

    col1.metric(
        "Artistas únicos",
        format_thousands(kpis["total_artists"]),
        delta=format_delta(float(kpis["total_artists"]), float(prev_total) if prev_total is not None else None),
        help="Artistas con al menos una canción en el dataset analizado",
    )
    col2.metric(
        "Popularidad promedio",
        f"{kpis['avg_popularity']} / 100",
        delta=format_delta(float(kpis["avg_popularity"]), float(prev_pop) if prev_pop is not None else None),
        help="Escala de 0 a 100 según Spotify",
    )
    col3.metric(
        "Contenido explícito",
        f"{kpis['explicit_percentage']}%",
        delta=format_delta(float(kpis["explicit_percentage"]), float(prev_exp) if prev_exp is not None else None),
    )
    col4.metric(
        "Duración media (min)",
        f"{kpis['avg_duration_min']}",
        delta=format_delta(float(kpis["avg_duration_min"]), float(prev_dur) if prev_dur is not None else None),
    )

    popularity_progress = max(0.0, min(float(kpis["avg_popularity"]) / 100.0, 1.0))
    st.markdown(
        f"""
        <div style=\"margin-top:0.25rem;margin-bottom:0.25rem;\">\
            <div style=\"height:8px;background:#2a2a2a;border-radius:999px;overflow:hidden;\">\
                <div style=\"width:{popularity_progress * 100:.2f}%;height:8px;background:#1DB954;\"></div>\
            </div>\
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.warning("No se pudieron cargar los KPIs.")

st.markdown("---")

# --- GRÁFICOS ---
trend_query_params = dict(query_params)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader(
        f"Top 10 canciones por popularidad mediana ({year_min}-{year_max})"
    )
    trend_data = fetch_section(
        "Tendencia de canciones",
        "/charts/trend-songs",
        params=trend_query_params,
        loading_text="Cargando tendencia de canciones",
    )
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        fig_bar = px.bar(
            df_trend, 
            x='median_popularity', 
            y='name', 
            orientation='h',
            labels={'median_popularity': 'Mediana Popularidad', 'name': 'Canción'},
            color_discrete_sequence=['#1DB954']
        )
        fig_bar.update_layout(template="spotify")
        st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("Relación entre danceability y energy")
    scatter_params = dict(query_params)
    scatter_params["sample_size"] = scatter_sample
    scatter_data = fetch_section(
        "Scatter danceability-energy",
        "/charts/dance-vs-energy",
        params=scatter_params,
        loading_text="Cargando scatter de audio features",
    )
    if scatter_data:
        df_scatter = pd.DataFrame(scatter_data)
        total_tracks = int((kpis or {}).get("total_tracks", len(df_scatter)))
        st.caption(
            f"Mostrando muestra aleatoria de {len(df_scatter):,} canciones de un catálogo de {total_tracks:,}; "
            f"se limita para mantener legible la nube de puntos."
        )
        fig_scatter = px.scatter(
            df_scatter, 
            x='danceability', 
            y='energy', 
            color='popularity',
            hover_name='name',
            color_continuous_scale=['#121212', '#1DB954']
        )
        fig_scatter.update_layout(
            template="spotify",
            coloraxis_colorbar=dict(
                title="Popularidad",
                ticksuffix=" pts",
            ),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
st.subheader("Evolución de la popularidad promedio por año")
trend_time_data = fetch_section(
    "Popularidad temporal",
    "/charts/popularity-over-time",
    params=query_params,
    loading_text="Cargando tendencia temporal",
)
if trend_time_data:
    df_time = pd.DataFrame(trend_time_data)
    df_time = df_time[(df_time["year"] >= year_range[0]) & (df_time["year"] <= year_range[1])]
    full_years = pd.DataFrame({"year": list(range(year_range[0], year_range[1] + 1))})
    df_time = full_years.merge(df_time, on="year", how="left")
    fig_time = px.line(
        df_time,
        x="year",
        y="avg_popularity",
        markers=True,
        labels={"year": "Año", "avg_popularity": "Popularidad promedio"},
    )
    fig_time.update_layout(template="spotify")
    fig_time.update_xaxes(autorange=True)
    fig_time.update_yaxes(range=[0, 100], title="Popularidad promedio")
    st.plotly_chart(fig_time, use_container_width=True)
