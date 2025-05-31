# recommendation/feature_engineering.py

"""
Funciones de ingeniería de características para el sistema de recomendación.
Incluye similaridad coseno y construcción de vectores de características
usando metadatos de películas o series.
"""

import numpy as np
from recommendation.config import WEIGHTS
from recommendation.nlp_utils import clean_overview

def cosine_similarity(vec_a, vec_b):
    """
    Calcula la similitud coseno entre dos vectores.

    Parámetros:
    - vec_a: numpy.ndarray, primer vector.
    - vec_b: numpy.ndarray, segundo vector.

    Devuelve:
    - float: valor de similitud coseno en [0, 1], o 0.0 si alguno es nulo.
    """
    dot = np.dot(vec_a, vec_b)
    na, nb = np.linalg.norm(vec_a), np.linalg.norm(vec_b)
    return dot / (na * nb) if na and nb else 0.0

def build_feature_vector(details,
                         all_genres, all_countries, all_companies, all_languages,
                         tfidf, PLATFORMS):
    """
    Construye un vector de características para una película o serie,
    combinando varios indicadores ponderados.

    Parámetros:
    - details: dict con metadatos de la obra (géneros, fechas, empresas, etc.).
    - all_genres: lista de todos los géneros posibles.
    - all_countries: lista de todos los países de origen posibles.
    - all_companies: lista de todas las compañías productoras.
    - all_languages: lista de idiomas originales posibles.
    - tfidf: objeto TfidfVectorizer para vectorizar el overview.
    - PLATFORMS: dict que mapea nombre de plataforma a lista de IDs disponibles.

    Devuelve:
    - numpy.ndarray: vector concatenado con todas las subcaracterísticas.
    """
    w = WEIGHTS

    # 1) Géneros
    genre_vec = np.zeros(len(all_genres))
    for g in details.get('genres', []):
        if g.get('name') in all_genres:
            genre_vec[all_genres.index(g['name'])] = 1.0
    genre_vec *= w['genre']

    # 2) Overview TF-IDF
    clean_text = clean_overview(details.get('overview', ''))
    tfidf_vec = tfidf.transform([clean_text]).toarray()[0] * w['overview']

    # 3) Disponibilidad en plataformas
    avail_vec = np.zeros(len(PLATFORMS))
    mid = details.get('id')
    for i, platform in enumerate(PLATFORMS):
        if mid in PLATFORMS[platform]:
            avail_vec[i] = 1.0
    avail_vec *= w['availability']

    # 4) Año / primera emisión
    year_vec = np.zeros(1)
    date = details.get('release_date') or details.get('first_air_date') or ''
    try:
        year = int(date[:4])
        norm = (year - 1900) / (2025 - 1900)
        year_vec[0] = min(max(norm, 0.0), 1.0) * w['year']
    except:
        pass

    # 5) Belongs to collection (nuevo)
    belongs = 1.0 if details.get('belongs_to_collection') else 0.0
    belongs_vec = np.array([belongs]) * w['collection']

    # 6) País de origen
    country_vec = np.zeros(len(all_countries))
    for c in details.get('origin_country', []):
        if c in all_countries:
            country_vec[all_countries.index(c)] = 1.0
    country_vec *= w['country']

    # 7) Compañías productoras
    comp_vec = np.zeros(len(all_companies))
    for pc in details.get('production_companies', []):
        name = pc.get('name')
        if name in all_companies:
            comp_vec[all_companies.index(name)] = 1.0
    comp_vec *= w['company']

    # 8) Popularidad
    pop = details.get('popularity') or 0
    pop_vec = np.array([min(max(pop / 100.0, 0.0), 1.0)]) * w['popularity']

    # 9) Voto medio
    vote = details.get('vote_average') or 0
    vote_vec = np.array([min(max(vote / 10.0, 0.0), 1.0)]) * w['vote_avg']

    # 10) Revenue
    rev = details.get('revenue') or 0
    rev_vec = np.array([min(max(rev / 1e9, 0.0), 1.0)]) * w['revenue']

    # 11) Idioma original
    lang_vec = np.zeros(len(all_languages))
    lang = details.get('original_language')
    if lang in all_languages:
        lang_vec[all_languages.index(lang)] = 1.0
    lang_vec *= w['orig_lang']

    # 12) Temporadas (solo series)
    seasons = details.get('number_of_seasons') or 0
    seasons_norm = min(max(seasons / 10.0, 0.0), 1.0)
    seasons_vec = np.array([seasons_norm]) * w.get('seasons', 0.0)

    # 13) Episodios (solo series)
    episodes = details.get('number_of_episodes') or 0
    episodes_norm = min(max(episodes / 100.0, 0.0), 1.0)
    episodes_vec = np.array([episodes_norm]) * w.get('episodes', 0.0)

    return np.concatenate([
        genre_vec,
        tfidf_vec,
        avail_vec,
        year_vec,
        belongs_vec,
        country_vec,
        comp_vec,
        pop_vec,
        vote_vec,
        rev_vec,
        lang_vec,
        seasons_vec,
        episodes_vec,
    ])
