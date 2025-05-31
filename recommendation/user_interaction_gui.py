# recommendation/user_interaction_gui.py


from tkinter import ttk, messagebox
import tkinter as tk
from recommendation.tmdb_client import search_movie_by_title
from recommendation.series_client import search_series_by_title
from recommendation.config import REFERENCE_MOVIES, REFERENCE_SERIES

# ---------------- Funciones de interacción de películas ----------------

def rate_movie(movie_id: int, title: str, user_ratings: dict, parent, callback):
    """
    Abre un diálogo modal para que el usuario puntúe una película.

    Parámetros:
    - movie_id: ID de TMDB de la película.
    - title: Título de la película para mostrar.
    - user_ratings: diccionario donde se almacenarán las puntuaciones {movie_id: rating}.
    - parent: ventana padre de Tkinter para centrar el diálogo.
    - callback: función a invocar una vez se ha guardado la puntuación.
    """
    # Creando ventana emergente
    window = tk.Toplevel(parent)
    window.title(f"Puntua {title}")
    window.geometry("400x200+760+440")
    window.configure(bg="#f0f0f0")

    # Etiqueta y campo de entrada
    tk.Label(window, text=f"Puntua {title} (0-5):", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    rating_var = tk.StringVar()
    entry = ttk.Entry(window, textvariable=rating_var, width=10, font=("Arial", 12))
    entry.pack(pady=10)
    
    def submit():
        try:
            rating = float(rating_var.get())
            if 0.0 <= rating <= 5.0:
                user_ratings[movie_id] = rating
                window.destroy()
                callback()
            else:
                messagebox.showerror("Error", "La puntuación debe ser entre 0 y 5", parent=window)
        except ValueError:
            messagebox.showerror("Error", "Porfavor introduce un número válido", parent=window)

    # Vincular Enter al envío 
    entry.bind("<Return>", lambda event: submit())
    entry.focus_set()
    # Botón de enviar
    ttk.Button(window, text="Puntuar", command=submit).pack(pady=10)

def add_movie_manually(user_ratings: dict, REFERENCE_MOVIES_CUSTOM: dict, parent, callback):
    """
    Abre un diálogo para buscar una película por título y añadirla manualmente.

    Parámetros:
    - user_ratings: diccionario de puntuaciones existente.
    - REFERENCE_MOVIES_CUSTOM: dict para almacenar referencias personalizadas {movie_id: title}.
    - parent: ventana padre.
    - callback: función a invocar tras añadir y puntuar.
    """
    window = tk.Toplevel(parent)
    window.title("Añadir Película")
    window.geometry("600x400+660+340")
    window.configure(bg="#f0f0f0")

    # Campo de búsqueda
    tk.Label(window, text="Nombre de la película:", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    name_var = tk.StringVar()
    entry = ttk.Entry(window, textvariable=name_var, width=30, font=("Arial", 12))
    entry.pack(pady=10)
    
    # Marco y lista de resultados
    results_frame = tk.Frame(window, bg="#f0f0f0")
    results_frame.pack(pady=10, fill="both", expand=True)
    results_listbox = tk.Listbox(results_frame, font=("Arial", 12), height=10, selectmode=tk.SINGLE, exportselection=False)
    results_listbox.pack(pady=10, padx=10, fill="both", expand=True)

    def search():
        """
        Realiza la búsqueda en TMDB y muestra resultados en la lista.
        """
        results_listbox.delete(0, tk.END)
        title = name_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Por favor introduce el nombre de la película", parent=window)
            return
        results = search_movie_by_title(title)
        if not results:
            messagebox.showerror("Error", "No se han encontrado resultados", parent=window)
            return
        for idx, m in enumerate(results[:10], 1):
            results_listbox.insert(tk.END, f"{idx}. {m.get('title', 'Unknown')} ({m.get('release_date', '¿?')})")
        results_listbox.results = results
        results_listbox.focus_set()
        if results:
            results_listbox.selection_set(0)
        print("Buscar resultados:", results)

    def select(event=None):
        try:
            idx = results_listbox.curselection()[0]
            sel = results_listbox.results[idx]
            if not sel.get("id") or not sel.get("title"):
                messagebox.showerror("Error", "La película seleccionada tiene datos invalidos", parent=window)
                return
            movie_id, title = sel["id"], sel["title"]
            print(f"Seleccionado: ID={movie_id}, Title={title}")  # Debug: Log selection
            REFERENCE_MOVIES_CUSTOM[movie_id] = title
            window.destroy()
            rate_movie(movie_id, title, user_ratings, parent, callback)
        except IndexError:
            messagebox.showerror("Error", "Por favor, selecciona una película de la lista", parent=window)
        except KeyError as e:
            messagebox.showerror("Error", f"Película invalida: no encontrada {str(e)}", parent=window)

    entry.bind("<Return>", lambda event: search())
    results_listbox.bind("<Return>", lambda event: select())
    results_listbox.bind("<Double-1>", lambda event: select())
    entry.focus_set()

    ttk.Button(window, text="Buscar", command=search).pack(pady=10)
    ttk.Button(window, text="Seleccionar", command=select).pack(pady=10)
    ttk.Button(window, text="Cancelar", command=window.destroy).pack(pady=10)

def modify_rating(user_ratings: dict, REFERENCE_MOVIES_CUSTOM: dict, parent, callback):
    """
    Abre un diálogo para modificar la puntuación de una película ya valorada.

    Lista solo las películas previamente puntuadas.
    """
    all_movies = {**REFERENCE_MOVIES, **REFERENCE_MOVIES_CUSTOM}
    rated_movies = {mid: title for mid, title in all_movies.items() if mid in user_ratings}

    window = tk.Toplevel(parent)
    window.title("Modificar puntuación de la película")
    window.geometry("600x400+660+340")
    window.configure(bg="#f0f0f0")

    tk.Label(window, text="Selecciona la película para modificar:", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    listbox = tk.Listbox(window, font=("Arial", 12), height=10, selectmode=tk.SINGLE, exportselection=False)
    listbox.pack(pady=10, padx=10, fill="both", expand=True)

    for mid, title in rated_movies.items():
        listbox.insert(tk.END, f"{title} -> Actual: {user_ratings[mid]}")
    listbox.rated_movies = list(rated_movies.items())

    def select(event=None):
        try:
            idx = listbox.curselection()[0]
            mid, title = listbox.rated_movies[idx]
            window.destroy()
            rate_movie(mid, title, user_ratings, parent, callback)
        except IndexError:
            messagebox.showerror("Error", "Por favor, seleccione una pelicula", parent=window)

    listbox.bind("<Return>", lambda event: select())
    listbox.bind("<Double-1>", lambda event: select())
    listbox.focus_set()
    if rated_movies:
        listbox.selection_set(0)  # Highlight first item

    ttk.Button(window, text="Seleccionar", command=select).pack(pady=10)
    ttk.Button(window, text="Cancelar", command=window.destroy).pack(pady=10)

# ---------------- Funciones de interacción de series ----------------

def rate_series(series_id: int, title: str, series_ratings: dict, parent, callback):
    """
    Abre un diálogo modal para que el usuario puntúe una serie.

    Parámetros:
    - series_id: ID de TMDB de la serie.
    - title: Nombre de la serie para mostrar.
    - series_ratings: diccionario donde se almacenarán las puntuaciones {series_id: rating}.
    - parent: ventana padre de Tkinter para centrar el diálogo.
    - callback: función a invocar una vez se ha guardado la puntuación.
    """
    window = tk.Toplevel(parent)
    window.title(f"Puntua {title}")
    window.geometry("400x200+760+440")
    window.configure(bg="#f0f0f0")

    tk.Label(window, text=f"Puntua {title} (0-5):", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    rating_var = tk.StringVar()
    entry = ttk.Entry(window, textvariable=rating_var, width=10, font=("Arial", 12))
    entry.pack(pady=10)
    
    def submit():
        try:
            rating = float(rating_var.get())
            if 0.0 <= rating <= 5.0:
                series_ratings[series_id] = rating
                window.destroy()
                callback()
            else:
                messagebox.showerror("Error", "La puntuación debe ser entre 0 y 5", parent=window)
        except ValueError:
            messagebox.showerror("Error", "Porfavor introduce un número válido", parent=window)
    
    entry.bind("<Return>", lambda event: submit())
    entry.focus_set()
    ttk.Button(window, text="Puntuar", command=submit).pack(pady=10)

def add_series_manually(series_ratings: dict, REFERENCE_SERIES_CUSTOM: dict, parent, callback):
    """
    Abre un diálogo para buscar una serie por nombre y añadirla manualmente.

    Parámetros:
    - series_ratings: diccionario de puntuaciones de series existentes.
    - REFERENCE_SERIES_CUSTOM: dict para almacenar referencias personalizadas {series_id: name}.
    - parent: ventana padre.
    - callback: función a invocar tras añadir y puntuar.
    """
    window = tk.Toplevel(parent)
    window.title("Añadir Serie")
    window.geometry("600x400+660+340")
    window.configure(bg="#f0f0f0")

    tk.Label(window, text="Introduce el nombre de la serie:", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    name_var = tk.StringVar()
    entry = ttk.Entry(window, textvariable=name_var, width=30, font=("Arial", 12))
    entry.pack(pady=10)
    
    results_frame = tk.Frame(window, bg="#f0f0f0")
    results_frame.pack(pady=10, fill="both", expand=True)
    results_listbox = tk.Listbox(results_frame, font=("Arial", 12), height=10, selectmode=tk.SINGLE, exportselection=False)
    results_listbox.pack(pady=10, padx=10, fill="both", expand=True)

    def search():
        results_listbox.delete(0, tk.END)
        title = name_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Por favor, introduce el nombre de la serie", parent=window)
            return
        results = search_series_by_title(title)
        if not results:
            messagebox.showerror("Error", "No se han encontrado resultados", parent=window)
            return
        for idx, s in enumerate(results[:10], 1):
            results_listbox.insert(tk.END, f"{idx}. {s.get('name', 'Unknown')} ({s.get('first_air_date', '¿?')})")
        results_listbox.results = results
        results_listbox.focus_set()
        if results:
            results_listbox.selection_set(0)
        print("Buscando resultados:", results)

    def select(event=None):
        try:
            idx = results_listbox.curselection()[0]
            sel = results_listbox.results[idx]
            if not sel.get("id") or not sel.get("name"):
                messagebox.showerror("Error", "La serie seleccionada tiene datos invalidos", parent=window)
                return
            series_id, name = sel["id"], sel["name"]
            print(f"Selected: ID={series_id}, Name={name}")  # Debug: Log selection
            REFERENCE_SERIES_CUSTOM[series_id] = name
            window.destroy()
            rate_series(series_id, name, series_ratings, parent, callback)
        except IndexError:
            messagebox.showerror("Error", "Por favor, selecciona una serie de la lista", parent=window)
        except KeyError as e:
            messagebox.showerror("Error", f"Serie invalida: no encontrada {str(e)}", parent=window)

    entry.bind("<Return>", lambda event: search())
    results_listbox.bind("<Return>", lambda event: select())
    results_listbox.bind("<Double-1>", lambda event: select())
    entry.focus_set()

    ttk.Button(window, text="Buscar", command=search).pack(pady=10)
    ttk.Button(window, text="Seleccionar", command=select).pack(pady=10)
    ttk.Button(window, text="Cancelar", command=window.destroy).pack(pady=10)

def modify_series_rating(series_ratings: dict, REFERENCE_SERIES_CUSTOM: dict, parent, callback):
    """
    Abre un diálogo para modificar la puntuación de una serie ya valorada.

    Lista solo las series previamente puntuadas.
    """
    # Combinar referencias base y personalizadas
    all_series = {**REFERENCE_SERIES, **REFERENCE_SERIES_CUSTOM}
    rated_series = {sid: name for sid, name in all_series.items() if sid in series_ratings}

    window = tk.Toplevel(parent)
    window.title("Modificar puntuación de la serie")
    window.geometry("600x400+660+340")
    window.configure(bg="#f0f0f0")

    tk.Label(window, text="Selecciona la serie para modificar:", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
    listbox = tk.Listbox(window, font=("Arial", 12), height=10, selectmode=tk.SINGLE, exportselection=False)
    listbox.pack(pady=10, padx=10, fill="both", expand=True)

    for sid, name in rated_series.items():
        listbox.insert(tk.END, f"{name} -> Actual: {series_ratings[sid]}")
    listbox.rated_series = list(rated_series.items())

    def select(event=None):
        """
        Reabre rate_series para la serie seleccionada.
        """
        try:
            idx = listbox.curselection()[0]
            sid, name = listbox.rated_series[idx]
            window.destroy()
            rate_series(sid, name, series_ratings, parent, callback)
        except IndexError:
            messagebox.showerror("Error", "Por favor selecciona una serie", parent=window)

    listbox.bind("<Return>", lambda event: select())
    listbox.bind("<Double-1>", lambda event: select())
    listbox.focus_set()
    if rated_series:
        listbox.selection_set(0)

    ttk.Button(window, text="Seleccionar", command=select).pack(pady=10)
    ttk.Button(window, text="Cancelar", command=window.destroy).pack(pady=10)