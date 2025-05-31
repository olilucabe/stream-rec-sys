# calibrate_weights.py

import random
import json
import argparse
import sys
import time
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Importamos catálogos y recomendación
from recommendation.data_utils import load_movie_platforms, load_series_platforms, load_artifacts
from recommendation.recommendation_engine import calculate_affinity
from recommendation.config import WEIGHTS

# Parámetros para catálogos pequeños
SMALL_CATALOG_THRESHOLD = 100
SMALL_CATALOG_USERS = 50

# -------------------------------------
# Generación de usuarios sintéticos
# -------------------------------------
def generate_synthetic_user(platform_name, PLATFORMS,
                            liked_n=10, noise_k=1,
                            like_rating=5.0, noise_rating=1.0):
    """
    Construye un perfil sintético:
      - liked_n ítems de la plataforma con valoración alta.
      - noise_k ítems de otras plataformas con valoración baja.
    """
    available = PLATFORMS[platform_name]
    n_liked = min(liked_n, len(available))
    liked = random.sample(available, n_liked)
    ratings = {mid: like_rating for mid in liked}

    other = [mid for p, ids in PLATFORMS.items() if p != platform_name for mid in ids]
    n_noise = min(noise_k, len(other))
    if n_noise > 0:
        noise = random.sample(other, n_noise)
        for mid in noise:
            ratings[mid] = noise_rating
    return ratings

# -------------------------------------
# Tarea de simulación individual
# -------------------------------------
def _simulate_task(block, provider, PLATFORMS, tfidf, base_n):
    """
    Simula base_n usuarios sintéticos para (bloque, proveedor).
    Devuelve: bloque, aciertos, total
    """
    # One-hot para este bloque
    orig = WEIGHTS.copy()
    for k in WEIGHTS:
        WEIGHTS[k] = 1.0 if k == block else 0.0

    # Determinamos número de usuarios según catálogo
    size = len(PLATFORMS[provider])
    n_u = base_n if size >= SMALL_CATALOG_THRESHOLD else SMALL_CATALOG_USERS
    correct = 0
    for _ in range(n_u):
        ratings = generate_synthetic_user(provider, PLATFORMS)
        _, best = calculate_affinity(ratings, tfidf, PLATFORMS)
        if best == provider:
            correct += 1
    # Restauramos pesos originales
    WEIGHTS.update(orig)
    return block, correct, n_u

# -------------------------------------
# Función principal
# -------------------------------------
def run_one_hot(n_users=500, processes=None, content_type='movies',
                use_gui=False, max_providers=None, fast=False):
    """
    Ejecuta la calibración one-hot.
    --users: base de usuarios sintéticos
    --processes: procesos paralelos
    --type: movies, series o both
    --max_providers: límite de proveedores
    --fast: modo rápido (n_users//5)
    --gui: mostrar GUI de progreso
    """
    # Cargamos catálogos según tipo
    if content_type == 'movies':
        movie = load_movie_platforms()
        series = {}
        tfidf = load_artifacts(content_type='movies')
    elif content_type == 'series':
        movie = {}
        series = load_series_platforms()
        tfidf = load_artifacts(content_type='series')
    else:  # both
        movie = load_movie_platforms()
        series = load_series_platforms()
        tfidf = load_artifacts(content_type='movies')  # placeholder
    # Fusionar ambos catálogos
    PLATFORMS = {**movie}
    for p, ids in series.items():
        PLATFORMS.setdefault(p, []).extend(ids)

    # Ajustamos el modo rápido
    base_n = n_users // 5 if fast else n_users

    # Seleccionamos los proveedores
    providers = list(PLATFORMS.keys())
    if max_providers and max_providers < len(providers):
        providers = random.sample(providers, max_providers)

    # Definimos bloques y tareas
    blocks = list(WEIGHTS.keys())
    total_tasks = len(blocks) * len(providers)
    num_procs = processes or multiprocessing.cpu_count()

    # Acumuladores
    sum_correct = {b: 0 for b in blocks}
    sum_total = {b: 0 for b in blocks}
    completed = 0
    start = time.time()

    # GUI opcional
    if use_gui:
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
        root.title('One-Hot Calibration')
        bar = ttk.Progressbar(root, maximum=total_tasks, length=500)
        bar.pack(padx=10, pady=5)
        label = ttk.Label(root, text=f'Tareas: 0/{total_tasks} ETA: calculando...')
        label.pack(padx=10, pady=(0,10))

        def update_gui(count, eta):
            bar['value'] = count
            label['text'] = f'Tareas: {count}/{total_tasks} ETA: {eta:.1f}s'

        def worker():
            nonlocal completed
            tasks = [(b, p, PLATFORMS, tfidf, base_n)
                     for b in blocks for p in providers]
            with ProcessPoolExecutor(max_workers=num_procs) as exe:
                futures = {exe.submit(_simulate_task, *t): t for t in tasks}
                for fut in as_completed(futures):
                    b, c, tot = fut.result()
                    sum_correct[b] += c
                    sum_total[b] += tot
                    completed += 1
                    elapsed = time.time() - start
                    eta = (elapsed / completed) * (total_tasks - completed)
                    root.after(0, update_gui, completed, eta)
            root.after(0, root.destroy)

        threading.Thread(target=worker, daemon=True).start()
        root.mainloop()
    else:
        from tqdm import tqdm
        tasks = [(b, p, PLATFORMS, tfidf, base_n)
                 for b in blocks for p in providers]
        print(f'Executing {total_tasks} tasks with {num_procs} processes...', file=sys.stderr)
        with ProcessPoolExecutor(max_workers=num_procs) as exe:
            futures = {exe.submit(_simulate_task, *t): t for t in tasks}
            for fut in tqdm(as_completed(futures), total=total_tasks,
                             desc='Progress', file=sys.stderr):
                b, c, tot = fut.result()
                sum_correct[b] += c
                sum_total[b] += tot

    # Calculamos exactitudes y pesos finales
    accuracies = {b: (sum_correct[b] / sum_total[b] if sum_total[b] else 0.0)
                  for b in blocks}
    total_acc = sum(accuracies.values()) or 1.0
    final_weights = {b: accuracies[b] / total_acc for b in blocks}
    one_hot_inputs = {b: {k: 1.0 if k == b else 0.0 for k in blocks} for b in blocks}

    # Guardamos resultados
    out = {
        'content_type': content_type,
        'n_users': n_users,
        'max_providers': max_providers,
        'fast_mode': fast,
        'processes': num_procs,
        'one_hot_inputs': one_hot_inputs,
        'accuracies': accuracies,
        'final_weights': final_weights,
        'processed_providers': providers
    }
    fn = f'one_hot_{content_type}_results.json'
    with open(fn, 'w') as f:
        json.dump(out, f, indent=2)
    print('Results saved to', fn)

# -------------------------------------
# Entrada principal
# -------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='One-hot calibration granular')
    parser.add_argument('--users', type=int, default=100,
                        help='Usuarios base por proveedor')
    parser.add_argument('--processes', type=int, default=None,
                        help='Procesos paralelos (default=CPU)')
    parser.add_argument('--type', choices=['movies','series','both'], default='movies',
                        help='Catálogo a usar')
    parser.add_argument('--gui', action='store_true',
                        help='Mostrar GUI de progreso')
    parser.add_argument('--max_providers', type=int, default=None,
                        help='Máximo proveedores a muestrear (reduce tareas)')
    parser.add_argument('--fast', action='store_true',
                        help='Modo rápido: reduce base de usuarios para acelerar')
    args = parser.parse_args()
    run_one_hot(n_users=args.users,
                processes=args.processes,
                content_type=args.type,
                use_gui=args.gui,
                max_providers=args.max_providers,
                fast=args.fast)

