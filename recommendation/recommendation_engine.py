# recommendation/recommendation_engine.py

"""
Motor de recomendaciones: calcula afinidad entre el perfil del usuario y las plataformas
(para películas, series o mixto) usando similitud coseno sobre vectores de características.
"""
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from recommendation.user_profile import build_user_profile, build_series_profile
from recommendation.tmdb_client import get_movie_details
from recommendation.series_client import get_series_details
from recommendation.feature_engineering import build_feature_vector, cosine_similarity


def calculate_affinity(user_ratings: dict,
                       tfidf,
                       PLATFORMS: dict) -> tuple:
    """
    Calcula la afinidad del usuario con cada plataforma de películas.

    1. Construye perfil de usuario a partir de sus calificaciones.
    2. Para cada plataforma, obtiene detalles de cada película disponible,
       genera su vector de características y mide similitud coseno con el perfil.
    3. Imprime score por plataforma y retorna el mejor resultado.

    Parámetros:
    - user_ratings: dict {movie_id: rating} con valoraciones del usuario.
    - tfidf: TfidfVectorizer para vectorizar overviews.
    - PLATFORMS: dict {platform_name: [movie_id, ...]}.

    Devuelve:
    - scores: dict {platform_name: avg_similarity}.
    - best: plataforma con mayor afinidad.
    """
    # 1) Construimos el perfil de usuario
    profile, genres, countries, companies, languages = build_user_profile(
        user_ratings, tfidf, PLATFORMS
    )
    print("\n=== AFINIDAD CON CADA PLATAFORMA ===")
    scores = {}
    best, best_score = None, -1

    # Función interna que calcula similitud promedio para una plataforma
    def platform_score(platform: str, ids: list) -> tuple:
        sims = []
        for mid in ids:
            det = get_movie_details(mid)
            if not det:
                continue  # omitir IDs fallidos
            vec = build_feature_vector(
                det, genres, countries, companies, languages,
                tfidf, PLATFORMS
            )
            sims.append(cosine_similarity(profile, vec))
        # media de similitudes (0 si no hay vídeos)
        return platform, np.mean(sims) if sims else 0.0

    # 2) Ejecución paralela usando ThreadPoolExecutor
    max_workers = min(32, len(PLATFORMS) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(platform_score, p, ids) for p, ids in PLATFORMS.items()]
        for fut in as_completed(futures):
            platform, avg = fut.result()
            scores[platform] = avg
            print(f"{platform}: {avg:.3f}")
            if avg > best_score:
                best, best_score = platform, avg

    # 3) Resultado recomendado
    print(f"\n✅ Plataforma recomendada: {best}\n")
    return scores, best


def calculate_series_affinity(series_ratings: dict,
                                tfidf,
                                PLATFORMS: dict) -> tuple:
    """
    Misma lógica que calculate_affinity, pero para series.

    Parámetros:
    - series_ratings: dict {series_id: rating}.
    - tfidf: TfidfVectorizer para overviews de series.
    - PLATFORMS: dict {platform_name: [series_id, ...]}.

    Devuelve:
    - scores: dict por plataforma.
    - best: plataforma con mayor afinidad.
    """
    # Construimos los perfil de series
    profile, genres, countries, companies, languages = build_series_profile(
        series_ratings, tfidf, PLATFORMS
    )
    print("\n=== AFINIDAD SERIES ===")
    scores = {}
    best, best_score = None, -1

    def platform_score(platform: str, ids: list) -> tuple:
        sims = []
        for sid in ids:
            det = get_series_details(sid)
            if not det:
                continue
            vec = build_feature_vector(
                det, genres, countries, companies, languages,
                tfidf, PLATFORMS
            )
            sims.append(cosine_similarity(profile, vec))
        return platform, np.mean(sims) if sims else 0.0

    max_workers = min(32, len(PLATFORMS) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(platform_score, p, ids) for p, ids in PLATFORMS.items()]
        for fut in as_completed(futures):
            platform, avg = fut.result()
            scores[platform] = avg
            print(f"{platform}: {avg:.3f}")
            if avg > best_score:
                best, best_score = platform, avg

    print(f"\n✅ Plataforma de series recomendada: {best}\n")
    return scores, best


def calculate_mix_affinity(user_ratings: dict,
                            series_ratings: dict,
                            tfidf,
                            movie_PLATFORMS: dict,
                            series_PLATFORMS: dict) -> tuple:
    """
    Calcula afinidad mixta considerando ambos contenidos:
    - Películas y series deben pertenecer a la misma plataforma para contarse.
    - Combina la media de afinidades de películas y series.

    Parámetros:
    - user_ratings: dict {movie_id: rating}
    - series_ratings: dict {series_id: rating}
    - tfidf: TfidfVectorizer para overviews.
    - movie_PLATFORMS: dict de películas.
    - series_PLATFORMS: dict de series.

    Devolvemos:
    - scores: dict {platform: mixed_score}.
    - best: plataforma mixta recomendada.
    """
    # Perfiles separados
    profile_m, g_m, c_m, co_m, l_m = build_user_profile(user_ratings, tfidf, movie_PLATFORMS)
    profile_s, g_s, c_s, co_s, l_s = build_series_profile(series_ratings, tfidf, series_PLATFORMS)

    print("\n=== AFINIDAD MIXTA (Películas + Series) ===")
    scores = {}
    best, best_score = None, -1
    # Solo plataformas comunes a ambos tipos
    common_platforms = set(movie_PLATFORMS).intersection(series_PLATFORMS)

    def mix_score(platform: str) -> tuple:
        # Afinidad películas
        sims_m = []
        for mid in movie_PLATFORMS[platform]:
            det = get_movie_details(mid)
            if not det:
                continue
            vec = build_feature_vector(det, g_m, c_m, co_m, l_m, tfidf, movie_PLATFORMS)
            sims_m.append(cosine_similarity(profile_m, vec))
        # Afinidad series
        sims_s = []
        for sid in series_PLATFORMS[platform]:
            det = get_series_details(sid)
            if not det:
                continue
            vec = build_feature_vector(det, g_s, c_s, co_s, l_s, tfidf, series_PLATFORMS)
            sims_s.append(cosine_similarity(profile_s, vec))
        # Media de ambas afinidades (considera 0 si vacío)
        avg_m = np.mean(sims_m) if sims_m else 0.0
        avg_s = np.mean(sims_s) if sims_s else 0.0
        return platform, (avg_m + avg_s) / 2

    max_workers = min(32, len(common_platforms) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(mix_score, p) for p in common_platforms]
        for fut in as_completed(futures):
            platform, score = fut.result()
            scores[platform] = score
            print(f"{platform}: {score:.3f}")
            if score > best_score:
                best, best_score = platform, score

    print(f"\n✅ Plataforma mixta recomendada: {best}\n")
    return scores, best
