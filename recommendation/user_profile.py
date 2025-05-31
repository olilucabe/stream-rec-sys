# recommendation/user_profile.py

import numpy as np
from recommendation.tmdb_client import get_movie_details
from recommendation.series_client import get_series_details
from recommendation.feature_engineering import build_feature_vector

def build_user_profile(user_ratings, tfidf, PLATFORMS):
    """
    Construye el perfil de usuario para PELÍCULAS,
    sin usar collection_matrix.
    """
    all_genres, all_countries, all_companies, all_languages = set(), set(), set(), set()
    cache = {}

    for mid, rating in user_ratings.items():
        det = get_movie_details(mid)
        if not det: continue
        cache[mid] = det
        for g in det.get('genres', []): all_genres.add(g.get('name'))
        for c in det.get('origin_country', []): all_countries.add(c)
        for pc in det.get('production_companies', []):
            if pc.get('name'): all_companies.add(pc['name'])
        if det.get('original_language'): all_languages.add(det['original_language'])

    all_genres, all_countries, all_companies, all_languages = map(list, 
        (all_genres, all_countries, all_companies, all_languages)
    )

    dim = (
        len(all_genres)
        + tfidf.get_feature_names_out().shape[0]
        + len(PLATFORMS)
        + 1   # año
        + 1   # belongs_to_collection
        + len(all_countries)
        + len(all_companies)
        + 1   # popularidad
        + 1   # voto medio
        + 1   # revenue
        + len(all_languages)
        + 1   # temporadas
        + 1   # episodios
    )

    profile = np.zeros(dim)
    weight_sum = 0.0

    for mid, rating in user_ratings.items():
        det = cache.get(mid)
        if not det: continue
        vec = build_feature_vector(
            det, all_genres, all_countries, all_companies, all_languages,
            tfidf, PLATFORMS
        )
        profile += rating * vec
        weight_sum += rating

    if weight_sum:
        profile /= weight_sum

    return profile, all_genres, all_countries, all_companies, all_languages

def build_series_profile(series_ratings, tfidf, PLATFORMS):
    """
    Igual que build_user_profile, pero para SERIES.
    """
    all_genres, all_countries, all_companies, all_languages = set(), set(), set(), set()
    cache = {}

    for sid, rating in series_ratings.items():
        det = get_series_details(sid)
        if not det: continue
        cache[sid] = det
        for g in det.get('genres', []): all_genres.add(g.get('name'))
        for c in det.get('origin_country', []): all_countries.add(c)
        for pc in det.get('production_companies', []):
            if pc.get('name'): all_companies.add(pc['name'])
        if det.get('original_language'): all_languages.add(det['original_language'])

    all_genres, all_countries, all_companies, all_languages = map(list, 
        (all_genres, all_countries, all_companies, all_languages)
    )

    dim = (
        len(all_genres)
        + tfidf.get_feature_names_out().shape[0]
        + len(PLATFORMS)
        + 1   # año
        + 1   # belongs_to_collection
        + len(all_countries)
        + len(all_companies)
        + 1   # popularidad
        + 1   # voto medio
        + 1   # revenue
        + len(all_languages)
        + 1   # temporadas
        + 1   # episodios
    )

    profile = np.zeros(dim)
    weight_sum = 0.0

    for sid, rating in series_ratings.items():
        det = cache.get(sid)
        if not det: continue
        vec = build_feature_vector(
            det, all_genres, all_countries, all_companies, all_languages,
            tfidf, PLATFORMS
        )
        profile += rating * vec
        weight_sum += rating

    if weight_sum:
        profile /= weight_sum

    return profile, all_genres, all_countries, all_companies, all_languages
