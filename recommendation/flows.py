# recommendation/flows.py

"""
Define los flujos de interacción GUI con Tkinter para recomendar:
- Películas
- Series
- Mixto (películas + series)
Utiliza menús, diálogos de configuración rápida/personalizada,
procesamiento en segundo plano y visualización de resultados.
"""

import tkinter as tk
from tkinter import ttk
import threading
import logging
from recommendation.data_utils import load_movie_platforms, load_series_platforms, load_artifacts
from recommendation.config import REFERENCE_MOVIES, REFERENCE_SERIES
from recommendation.user_interaction_gui import (
    rate_movie, add_movie_manually, modify_rating,
    rate_series, add_series_manually, modify_series_rating
)
from recommendation.recommendation_engine import (
    calculate_affinity, calculate_series_affinity, calculate_mix_affinity
)

# Configurar logging para debug
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def clear_window(window):
    """
    Elimina todos los widgets del contenedor dado.
    """
    for widget in window.winfo_children():
        widget.destroy()

def disable_widgets(window):
    """
    Deshabilita todos los widgets interactivos (botones, entradas, combobox)
    y recorre recursivamente frames o labelframes dentro del contenedor.
    """
    for widget in window.winfo_children():
        if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox)):
            widget.configure(state="disabled")
        elif isinstance(widget, (tk.Frame, tk.LabelFrame)):
            disable_widgets(widget)

def enable_widgets(window):
    """
    Habilita todos los widgets interactivos previamente deshabilitados.
    """
    for widget in window.winfo_children():
        if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox)):
            widget.configure(state="normal")
        elif isinstance(widget, (tk.Frame, tk.LabelFrame)):
            enable_widgets(widget)

def show_affinity_results(scores, title, window, back_callback):
    """
    Muestra los resultados de afinidad:
    - Encabezado con el título.
    - Si no hay scores, mensaje de error.
    - Top 30 plataformas: la mejor en grande, el resto en grid de 2 columnas.
    - Botón "Back" para volver al menú anterior.
    """
    try:
        clear_window(window)
        window.title(title)
        window.configure(bg="#f0f0f0")
        # Título principal
        tk.Label(window, text=title, font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=30)

        if not scores:
             # Ningún puntaje disponible
            tk.Label(window, text="Puntuacion de afinidad no disponible", font=("Arial", 14), fg="red", bg="#f0f0f0").pack(pady=20)
        else:
            # Ordenar y truncar top 30
            sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:30]
            
            # Mostrar la mejor plataforma destacada
            top_platform, top_score = sorted_platforms[0]
            tk.Label(
                window,
                text=f"1. {top_platform}: {top_score:.3f}",
                font=("Arial", 28, "bold"),
                bg="#d1e7ff",
                fg="#000000",
                pady=20,
                padx=20,
                relief="raised",
                borderwidth=2
            ).pack(pady=20, padx=50, fill="x")

            # Mostrar el resto en grid 2 columnas
            if len(sorted_platforms) > 1:
                grid_frame = tk.Frame(window, bg="#f0f0f0")
                grid_frame.pack(pady=20)

                columns = 2
                for idx, (platform, score) in enumerate(sorted_platforms[1:], 2):
                    row = (idx - 2) // columns
                    col = (idx - 2) % columns
                    tk.Label(
                        grid_frame,
                        text=f"{idx}. {platform}: {score:.3f}",
                        font=("Arial", 14),
                        bg="#f0f0f0",
                        anchor="w",
                        width=30
                    ).grid(row=row, column=col, padx=20, pady=5, sticky="w")
        # Botón de retroceso
        ttk.Button(window, text="Back", command=back_callback).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en show_affinity_results: {str(e)}")
        tk.Label(window, text=f"Error mostrando resultados: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def show_loading_screen(window):
    """
    Muestra un overlay con barra de progreso durante operaciones en segundo plano.

    Parámetros:
    - window: ventana principal de Tkinter.

    Retorna:
    - loading_frame: Frame semi-transparente mostrado, o None si falla.
    """
    try:
        # Deshabilitar widgets durante carga
        disable_widgets(window)
        
        # Marco que cubre toda la ventana
        loading_frame = tk.Frame(window, bg="gray")
        loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Contenido centrado
        content_frame = tk.Frame(loading_frame, bg="#f0f0f0")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(content_frame, text="Calculando puntuación de afinidad...", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
        progress = ttk.Progressbar(content_frame, mode="indeterminate", length=200)
        progress.pack(pady=10)
        progress.start(10)

        window.update()
        return loading_frame
    except Exception as e:
        logging.error(f"Error en show_loading_screen: {str(e)}")
        enable_widgets(window)
        tk.Label(window, text=f"Error: Fallo al mostrar la pantalla de carga: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
        return None

def destroy_loading_screen(loading_frame, window):
    """
    Elimina el overlay de carga y vuelve a habilitar widgets.
    """
    try:
        if loading_frame and isinstance(loading_frame, tk.Frame):
            loading_frame.destroy()
            enable_widgets(window)
    except Exception as e:
        logging.error(f"Error en destroy_loading_screen: {str(e)}")
        enable_widgets(window)

# ======== MOVIES FLOW ========

def quick_setup_movies_gui(window, user_ratings, custom_ref, secondary_callback):
    """
    Configuración rápida GUI para películas:
    - Presenta secuencialmente los primeros 10 títulos de REFERENCE_MOVIES.
    - Llama a rate_movie en ventana para cada uno.
    - Al completar, ofrece añadir más o ir al menú secundario.

    Parámetros:
    - window: ventana principal.
    - user_ratings: diccionario donde se almacenan puntuaciones.
    - custom_ref: referencias personalizadas.
    - secondary_callback: función para volver al menú secundario.
    """
    try:
        clear_window(window)
        window.title("Configuración Rapida - Películas")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Puntuando Películas", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def rate_next_movie(index=0):
            if index < min(10, len(REFERENCE_MOVIES)):
                mid, title = list(REFERENCE_MOVIES.items())[index]
                rate_movie(mid, title, user_ratings, window, lambda: rate_next_movie(index + 1))
            else:
                show_add_more_prompt()

        def show_add_more_prompt():
            clear_window(window)
            tk.Label(window, text="Quieres añadir mas peliculas?", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            ttk.Button(window, text="Si", command=add_movie_gui).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="No", command=secondary_callback).pack(pady=10, padx=400, fill="x")

        def add_movie_gui():
            clear_window(window)
            add_movie_manually(user_ratings, custom_ref, window, show_add_more_prompt)

        rate_next_movie()
    except Exception as e:
        logging.error(f"Error en quick_setup_movies_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def custom_setup_movies_gui(window, user_ratings, custom_ref, secondary_callback):
    """
    Configuración personalizada GUI para películas:
    - Permite añadir manualmente hasta obtener 10 valoraciones.
    - Muestra contador de selecciones.

    Parámetros:
    - window: ventana principal.
    - user_ratings: dict de puntuaciones actuales.
    - custom_ref: dict de referencias personalizadas.
    - secondary_callback: callback al terminar (10 ratings).
    """
    try:
        clear_window(window)
        window.title("Configuración personalizada - Películas")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text=f"Películas seleccionadas: {len(user_ratings)}/10", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
        
        def add_movie_gui():
            if len(user_ratings) < 10:
                clear_window(window)
                tk.Label(window, text=f"Películas seleccionadas: {len(user_ratings)}/10", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
                add_movie_manually(user_ratings, custom_ref, window, add_movie_gui)
            else:
                secondary_callback()

        add_movie_gui()
    except Exception as e:
        logging.error(f"Error en custom_setup_movies_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def secondary_menu_movies(window, user_ratings, custom_ref, main_menu_callback):
    """
    Menú secundario GUI para películas:
    - Ofrece calcular afinidad, modificar valoraciones, añadir más o volver al menú inicial.
    - Cada acción refresca la ventana o muestra pantalla de carga si es computacional.

    Parámetros:
    - window: ventana principal.
    - user_ratings: dict con puntuaciones actuales.
    - custom_ref: dict de referencias personalizadas.
    - main_menu_callback: callback para volver al menú principal.
    """
    try:
        clear_window(window)
        window.title("Películas")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Películas", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        PLATFORMS = load_movie_platforms()
        tfidf = load_artifacts()

        def calculate():
            if not user_ratings:
                tk.Label(window, text="Error: No hay películas puntuadas", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return
            if not PLATFORMS or not tfidf:
                tk.Label(window, text="Error: Error al cargar plataformas o tfidf", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return

            loading_frame = show_loading_screen(window)
            if not loading_frame:
                return
            window.update()

            def compute():
                try:
                    logging.info("Comenzando cálculo de afinidad")
                    scores, best = calculate_affinity(user_ratings, tfidf, PLATFORMS)
                    logging.info(f"Puntuaciones de afinidad: {scores}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        show_affinity_results(scores, "Afinidad de plataformas para películas", window, lambda: secondary_menu_movies(window, user_ratings, custom_ref, main_menu_callback))
                    ])
                except Exception as e:
                    logging.error(f"Error en el cálculo de afinidad: {str(e)}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        tk.Label(window, text=f"Error: Error en el cálculo de afinidad: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                    ])

            threading.Thread(target=compute, daemon=True).start()
        # Botones de acción
        ttk.Button(window, text="Calcular afinidad", command=calculate).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Modificar puntuaciones", command=lambda: modify_rating(user_ratings, custom_ref, window, lambda: secondary_menu_movies(window, user_ratings, custom_ref, main_menu_callback))).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Añadir mas películas", command=lambda: add_movie_manually(user_ratings, custom_ref, window, lambda: secondary_menu_movies(window, user_ratings, custom_ref, main_menu_callback))).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=lambda: movies_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en secondary_menu_movies: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def movies_flow(window, main_menu_callback):
    """
    Flujo inicial GUI para películas:
    - Muestra opciones de configuración rápida o personalizada.
    - Inicia el subflujo correspondiente.

    Parámetros:
    - window: ventana principal.
    - main_menu_callback: callback para volver al menú principal.
    """
    try:
        clear_window(window)
        window.title("Recomendación de Películas")
        window.configure(bg="#f0f0f0")

        user_ratings = {}
        custom_ref = {}

        tk.Label(window, text="Peliculas", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def secondary_callback():
            secondary_menu_movies(window, user_ratings, custom_ref, main_menu_callback)

        ttk.Button(window, text="Configuración Rápida", command=lambda: quick_setup_movies_gui(window, user_ratings, custom_ref, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Configuración Personalizada", command=lambda: custom_setup_movies_gui(window, user_ratings, custom_ref, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=main_menu_callback).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en movies_flow: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

# ======== SERIES FLOW ========

def quick_setup_series_gui(window, series_ratings, custom_ref, secondary_callback):
    """
    Configuración rápida GUI para series:
    - Puntúa los primeros 10 títulos de REFERENCE_SERIES.
    - Tras puntuar, ofrece añadir más o ir al menú secundario.
    """
    try:
        clear_window(window)
        window.title("Configuración Rapida - Series")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Puntuando Series", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def rate_next_series(index=0):
            if index < min(10, len(REFERENCE_SERIES)):
                sid, name = list(REFERENCE_SERIES.items())[index]
                rate_series(sid, name, series_ratings, window, lambda: rate_next_series(index + 1))
            else:
                show_add_more_prompt()

        def show_add_more_prompt():
            clear_window(window)
            tk.Label(window, text="Quieres añadir mas series?", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            ttk.Button(window, text="Si", command=add_series_gui).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="No", command=secondary_callback).pack(pady=10, padx=400, fill="x")

        def add_series_gui():
            clear_window(window)
            add_series_manually(series_ratings, custom_ref, window, show_add_more_prompt)

        rate_next_series()
    except Exception as e:
        logging.error(f"Error en quick_setup_series_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def custom_setup_series_gui(window, series_ratings, custom_ref, secondary_callback):
    """
    Configuración personalizada GUI para series:
    - Permite al usuario añadir manualmente hasta 10 series.
    - Muestra contador de series actuales.
    """
    try:
        clear_window(window)
        window.title("Configuración Personalizada - Series")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text=f"Series seleccionadas: {len(series_ratings)}/10", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
        
        def add_series_gui():
            if len(series_ratings) < 10:
                clear_window(window)
                tk.Label(window, text=f"Series seleccionadas: {len(series_ratings)}/10", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
                add_series_manually(series_ratings, custom_ref, window, add_series_gui)
            else:
                secondary_callback()

        add_series_gui()
    except Exception as e:
        logging.error(f"Error en custom_setup_series_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def secondary_menu_series(window, series_ratings, custom_ref, main_menu_callback):
    """
    Menú secundario GUI para series:
    - Calcula afinidad, permite modificar o añadir series, o volver.
    """
    try:
        clear_window(window)
        window.title("Series")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Series", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        PLATFORMS = load_series_platforms()
        tfidf = load_artifacts(content_type="series")

        def calculate():
            if not series_ratings:
                tk.Label(window, text="Error: No series rated", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return
            if not PLATFORMS or not tfidf:
                tk.Label(window, text="Error: Error al cargar plataformas o tfidf", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return

            loading_frame = show_loading_screen(window)
            if not loading_frame:
                return
            window.update()

            def compute():
                try:
                    logging.info("Comanzando el cálculo de affinidad de series")
                    scores, best = calculate_series_affinity(series_ratings, tfidf, PLATFORMS)
                    logging.info(f"Puntuación de afinidad de series: {scores}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        show_affinity_results(scores, "Afinidad de plataformas de series", window, lambda: secondary_menu_series(window, series_ratings, custom_ref, main_menu_callback))
                    ])
                except Exception as e:
                    logging.error(f"Error en el cálculo de afinidad de series: {str(e)}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        tk.Label(window, text=f"Error: Error en el cálculo de afinidad de series: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                    ])

            threading.Thread(target=compute, daemon=True).start()

        ttk.Button(window, text="Calcular afinidad", command=calculate).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Modificar puntuaciones", command=lambda: modify_series_rating(series_ratings, custom_ref, window, lambda: secondary_menu_series(window, series_ratings, custom_ref, main_menu_callback))).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Añadir mas series", command=lambda: add_series_manually(series_ratings, custom_ref, window, lambda: secondary_menu_series(window, series_ratings, custom_ref, main_menu_callback))).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=lambda: series_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en secondary_menu_series: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def series_flow(window, main_menu_callback):
    """
    Flujo inicial GUI para series:
    - Ofrece configuración rápida o personalizada.
    """
    try:
        clear_window(window)
        window.title("Recomendación de series")
        window.configure(bg="#f0f0f0")

        series_ratings = {}
        custom_ref = {}

        tk.Label(window, text="Series", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def secondary_callback():
            secondary_menu_series(window, series_ratings, custom_ref, main_menu_callback)

        ttk.Button(window, text="Configuración Rápida", command=lambda: quick_setup_series_gui(window, series_ratings, custom_ref, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Configuración Personalizada", command=lambda: custom_setup_series_gui(window, series_ratings, custom_ref, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=main_menu_callback).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en series_flow: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

# ======== MIX FLOW ========

def quick_setup_mix_gui(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, secondary_callback):
    """
    Configuración rápida GUI combinada:
    - Puntúa 5 películas y 5 series.
    - Ofrece añadir contenido adicional al finalizar.
    """
    try:
        clear_window(window)
        window.title("Configuración Rápida - Ambos")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Puntuando Películas y Series", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def rate_next_movie(index=0):
            if index < min(5, len(REFERENCE_MOVIES)):
                mid, title = list(REFERENCE_MOVIES.items())[index]
                rate_movie(mid, title, user_ratings, window, lambda: rate_next_movie(index + 1))
            else:
                rate_next_series(0)

        def rate_next_series(index=0):
            if index < min(5, len(REFERENCE_SERIES)):
                sid, name = list(REFERENCE_SERIES.items())[index]
                rate_series(sid, name, series_ratings, window, lambda: rate_next_series(index + 1))
            else:
                show_add_more_prompt()

        def show_add_more_prompt():
            clear_window(window)
            tk.Label(window, text="Añadir películas o series?", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            ttk.Button(window, text="Película", command=add_movie_gui).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Series", command=add_series_gui).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Hecho", command=secondary_callback).pack(pady=10, padx=400, fill="x")

        def add_movie_gui():
            clear_window(window)
            add_movie_manually(user_ratings, custom_ref_movies, window, show_add_more_prompt)

        def add_series_gui():
            clear_window(window)
            add_series_manually(series_ratings, custom_ref_series, window, show_add_more_prompt)

        rate_next_movie()
    except Exception as e:
        logging.error(f"Error en quick_setup_mix_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def custom_setup_mix_gui(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, secondary_callback):
    """
    Configuración personalizada GUI mixta:
    - Recoge 5 valoraciones de películas y 5 de series manualmente.
    """
    try:
        clear_window(window)
        window.title("Configuración Personalizada - Ambos")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text=f"Películas seleccionadas: {len(user_ratings)}/5", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
        
        def add_movie_gui():
            if len(user_ratings) < 5:
                clear_window(window)
                tk.Label(window, text=f"Películas seleccionadas: {len(user_ratings)}/5", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
                add_movie_manually(user_ratings, custom_ref_movies, window, add_movie_gui)
            else:
                add_series_gui()

        def add_series_gui():
            if len(series_ratings) < 5:
                clear_window(window)
                tk.Label(window, text=f"Series seleccionadas: {len(series_ratings)}/5", font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
                add_series_manually(series_ratings, custom_ref_series, window, add_series_gui)
            else:
                secondary_callback()

        add_movie_gui()
    except Exception as e:
        logging.error(f"Error en custom_setup_mix_gui: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback):
    """
    Menú secundario GUI mixto:
    - Calcula afinidad combinada o permite modificar/añadir contenido.
    """
    try:
        clear_window(window)
        window.title("Ambas")
        window.configure(bg="#f0f0f0")

        tk.Label(window, text="Ambas", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        movie_PLATFORMS = load_movie_platforms()
        series_PLATFORMS = load_series_platforms()
        tfidf = load_artifacts()

        def calculate():
            if not user_ratings or not series_ratings:
                tk.Label(window, text="Error: Películas o serie no puntuada", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return
            if not movie_PLATFORMS or not series_PLATFORMS or not tfidf:
                tk.Label(window, text="Error: Error al cargar plataformas o tfidf", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                return

            loading_frame = show_loading_screen(window)
            if not loading_frame:
                return
            window.update()

            def compute():
                try:
                    logging.info("Comenzando cálculo de afinidad de ambas")
                    scores, best = calculate_mix_affinity(user_ratings, series_ratings, tfidf, movie_PLATFORMS, series_PLATFORMS)
                    logging.info(f"Puntuación de afinidad de ambas: {scores}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        show_affinity_results(scores, "Afinidad de plataforma de ambas", window, lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback))
                    ])
                except Exception as e:
                    logging.error(f"Error en el cálculo de afinidad de ambas: {str(e)}")
                    window.after(0, lambda: [
                        destroy_loading_screen(loading_frame, window),
                        tk.Label(window, text=f"Error: Error en el cálculo de afinidad: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)
                    ])

            threading.Thread(target=compute, daemon=True).start()

        def modify():
            clear_window(window)
            tk.Label(window, text="Modificar puntuación de película o series?", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            ttk.Button(window, text="Película", command=lambda: modify_rating(user_ratings, custom_ref_movies, window, lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback))).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Series", command=lambda: modify_series_rating(series_ratings, custom_ref_series, window, lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback))).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Atras", command=lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback)).pack(pady=10, padx=400, fill="x")

        def add():
            clear_window(window)
            tk.Label(window, text="Añadir película o serie?", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            ttk.Button(window, text="Película", command=lambda: add_movie_manually(user_ratings, custom_ref_movies, window, lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback))).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Series", command=lambda: add_series_manually(series_ratings, custom_ref_series, window, lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback))).pack(pady=10, padx=400, fill="x")
            ttk.Button(window, text="Atras", command=lambda: secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback)).pack(pady=10, padx=400, fill="x")

        ttk.Button(window, text="Calcular afinidad", command=calculate).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Modificar puntuación", command=modify).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Añadir mas contenido", command=add).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=lambda: mix_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en secondary_menu_mix: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

def mix_flow(window, main_menu_callback):
    """
    Flujo inicial GUI mixto:
    - Muestra opciones de configuración rápida o personalizada.
    """
    try:
        clear_window(window)
        window.title("Recomendación de Películas y Series")
        window.configure(bg="#f0f0f0")

        user_ratings = {}
        series_ratings = {}
        custom_ref_movies = {}
        custom_ref_series = {}

        tk.Label(window, text="Ambos", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)

        def secondary_callback():
            try:
                secondary_menu_mix(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, main_menu_callback)
            except Exception as e:
                logging.error(f"Error en secondary_callback: {str(e)}")
                tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)

        ttk.Button(window, text="Configuración Rapida", command=lambda: quick_setup_mix_gui(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Configuración Personalizada", command=lambda: custom_setup_mix_gui(window, user_ratings, series_ratings, custom_ref_movies, custom_ref_series, secondary_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Atras", command=main_menu_callback).pack(pady=20, padx=400, fill="x")
    except Exception as e:
        logging.error(f"Error en mix_flow: {str(e)}")
        tk.Label(window, text=f"Error: {str(e)}", font=("Arial", 12), fg="red", bg="#f0f0f0").pack(pady=10)