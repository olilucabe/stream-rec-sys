# recommendation/data_utils.py

"""
Utilidades para cargar datos y artefactos del proyecto de recomendación.
Incluye funciones para leer proveedores desde Excel y cargar modelos preentrenados.
"""

import os
import joblib
import pandas as pd

def load_platforms_from_excel(filepath):
    """
    Lee un archivo Excel con información de proveedores y devuelve un diccionario
    que mapea cada proveedor a la lista de IDs de películas o series disponibles.

    Parámetros:
    - filepath: ruta al archivo Excel con columnas 'proveedor', 'movie_id' y 'tipo'.

    Devuelve:
    - dict: { proveedor1: [movie_id, movie_id, ...], proveedor2: [...] }
    """
    df = pd.read_excel(filepath)
    df = df[df["tipo"] == 1]
    platforms = {}
    for provider, group in df.groupby("proveedor"):
        platforms[provider] = group["movie_id"].tolist()
    return platforms

def load_artifacts(base_dir="DATA", content_type="movies"):
    """
    Carga el vectorizador TF-IDF correspondiente a películas o series.

    Parámetros:
    - base_dir: directorio base donde reside la carpeta DATA.
    - content_type: 'movies' o 'series', indica qué vectorizador cargar.

    Devuelve:
    - tfidf: objeto TfidfVectorizer cargado desde un archivo .pkl.
    """
    if content_type == "series":
        tfidf_path = os.path.join(base_dir, "OVERVIEW", "SERIES", "tfidf_vectorizer.pkl")
    else:
        tfidf_path = os.path.join(base_dir, "OVERVIEW", "tfidf_vectorizer.pkl")
    tfidf = joblib.load(tfidf_path)
    return tfidf

def load_movie_platforms():
    """
    Carga el diccionario de plataformas de películas desde el Excel.

    Devuelve:
    - dict: mapea proveedor a lista de movie_id.
    """
    filepath = os.path.join(
        "DATA", "MOVIES", "PROVEEDORES", "resultado_proveedoresBINARI.xlsx"
    )
    return load_platforms_from_excel(filepath)

def load_series_platforms():
    """
    Carga el diccionario de plataformas de series desde el Excel.

    Devuelve:
    - dict: mapea proveedor a lista de series_id.
    """
    filepath = os.path.join(
        "DATA", "SERIES", "PROVEEDORES", "tv_series_PROVEEDORES_BINARI.xlsx"
    )
    return load_platforms_from_excel(filepath)
