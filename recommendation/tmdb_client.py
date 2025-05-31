# recommendation/tmdb_client.py

"""
Módulo para obtener detalles y buscar películas en TMDB con reintentos y caché en memoria.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import TMDB_API_KEY
from recommendation.config import TMDB_API_KEY

# Configuramos una sesión compartida con política de reintentos para llamadas a la API de TMDB
_movie_session = requests.Session()
_movie_retry = Retry(
    total=3,            # Número total de reintentos
    backoff_factor=0.3,  # Tiempo de espera exponencial entre reintentos
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
_movie_adapter = HTTPAdapter(max_retries=_movie_retry)
_movie_session.mount("https://", _movie_adapter)
_movie_session.mount("http://", _movie_adapter)

# Caché en memoria para los detalles de las películas
_movie_details_cache = {}


def get_movie_details(movie_id: int):
    """
    Obtiene los detalles de una película por su ID:
    - Consulta la API de TMDB usando la sesión con reintentos.
    - Almacena en caché el resultado para llamadas posteriores.

    Parámetros:
    - movie_id: int, ID de la película en TMDB.

    Devuelve:
    - dict con los datos de la película si la petición es exitosa.
    - None en caso de error o timeout.
    """
    if movie_id in _movie_details_cache:
        return _movie_details_cache[movie_id]

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_API_KEY
    }

    try:
        resp = _movie_session.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        _movie_details_cache[movie_id] = data
        return data
    except requests.RequestException:
        return None


def search_movie_by_title(query: str):
    """
    Busca películas por título en TMDB:
    - Usa la sesión con reintentos y timeout.

    Parámetros:
    - query: str, término de búsqueda.

    Devuelve:
    - List[dict] con las películas encontradas.
    - Lista vacía en caso de error.
    """
    url = f"https://api.themoviedb.org/3/search/movie?query={query}&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_API_KEY
    }

    try:
        resp = _movie_session.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.RequestException:
        return []
