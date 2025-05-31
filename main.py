# main.py

import tkinter as tk
from tkinter import ttk
from recommendation.flows import movies_flow, series_flow, mix_flow

# Función principal para inicializar la GUI de recomendaciones

def main():
    window = tk.Tk()
    window.title("SISTEMA DE RECOMENDACIONES PARA SERVICIOS DE STREAMING")
    window.geometry("1920x1080")
    window.configure(bg="#f0f0f0")

    window.update_idletasks()
    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()
    x = (width - 1920) // 2
    y = (height - 1080) // 2
    window.geometry(f"1920x1080+{x}+{y}")

    def main_menu_callback():
        for widget in window.winfo_children():
            widget.destroy()
        tk.Label(window, text="SISTEMA DE RECOMENDACIONES PARA SERVICIOS DE STREAMING", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)
        ttk.Button(window, text="Películas", command=lambda: movies_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Series", command=lambda: series_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Ambos", command=lambda: mix_flow(window, main_menu_callback)).pack(pady=20, padx=400, fill="x")
        ttk.Button(window, text="Salir", command=window.quit).pack(pady=20, padx=400, fill="x")

    main_menu_callback()
    window.mainloop()

if __name__ == "__main__":
    main()