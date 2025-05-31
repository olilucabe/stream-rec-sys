# recommendation/series_client.py

"""
Módulo para obtener detalles y buscar series en TMDB con reintentos y caché en memoria.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from recommendation.config import TMDB_API_KEY

# Configuramos una sesión compartida con política de reintentos para llamadas a la API de TMDB
_series_session = requests.Session()
_series_retry = Retry(
    total=3,  # Número total de reintentos
    backoff_factor=0.3,  # Tiempo de espera exponencial entre reintentos
    status_forcelist=[429, 500, 502, 503, 504],  # Códigos HTTP que disparan un reintento
    allowed_methods=["GET"]  # Solo reenviar peticiones GET
)
_series_adapter = HTTPAdapter(max_retries=_series_retry)
# Montamos el adaptador en ambos esquemas (HTTP y HTTPS)
_series_session.mount("https://", _series_adapter)
_series_session.mount("http://", _series_adapter)

# Caché en memoria para no repetir peticiones a la misma serie
_series_cache = {}

def get_series_details(series_id: int):
    """
    Obtiene los detalles de una serie por su ID:
    - Consulta la API de TMDB usando la sesión con reintentos.
    - Almacena en caché el resultado para llamadas posteriores.

    Parámetros:
    - series_id: int, ID de la serie en TMDB.

    Devuelve:
    - dict con los datos de la serie si la petición es exitosa.
    - None en caso de error.
    """
    # Devolvemos de la caché si ya se consultó esta serie
    if series_id in _series_cache:
        return _series_cache[series_id]

    # Construimos la URL de la petición
    url = f"https://api.themoviedb.org/3/tv/{series_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_API_KEY
    }


    try:
        # Realizamos la petición con un timeout razonable
        resp = _series_session.get(url, headers=headers, timeout=5)
        resp.raise_for_status()  # Lanza excepción si el status no es 2xx
        data = resp.json()  # Parseamos la respuesta JSON
        # Guardamos en caché para uso futuro
        _series_cache[series_id] = data
        return data
    except requests.RequestException:
        # En caso de error de red o HTTP, devolvemos None
        return None


def search_series_by_title(query: str):
    """
    Busca series por título en TMDB:
    - Realiza una petición de búsqueda y devuelve los resultados.

    Parámetros:
    - query: str, término de búsqueda (título parcial o completo).

    Devuelve:
    - List[dict] con las series encontradas.
    - Lista vacía si hay error de petición.
    """
    # Construimos la URL de búsqueda con parámetros de consulta
    url = f"https://api.themoviedb.org/3/search/tv?query={query}&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_API_KEY
    }

    try:
        resp = _series_session.get(url, headers=headers, timeout=5)
        resp.raise_for_status()  # Verificamos código de estado
        results = resp.json().get("results", [])  # Extraemos la lista de resultados
        return results
    except requests.RequestException:
        # En caso de fallo devolvemos lista vacía
        return []
