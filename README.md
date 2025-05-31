# Sistema de Recomendación de Plataformas de Streaming

Este proyecto es un sistema de recomendación inteligente que, basado en tus gustos de películas y series, te sugiere la mejor plataforma de streaming donde encontrarás más contenido alineado a tus preferencias. Utiliza información de TMDB, aprendizaje basado en afinidad y calibración de características para mejorar la precisión de las recomendaciones.


## ¿Cómo Funciona?

El sistema construye un perfil vectorial del usuario basado en las películas o series que califica. Cada título es representado mediante un vector de características (género, idioma, popularidad, sinopsis vectorizada, etc.) y luego se calcula un promedio ponderado por puntuación. Este perfil se compara con los catálogos de cada plataforma usando similitud coseno, identificando así la más afín.

## Cómo Ejecutarlo

### Requisitos

- Python ≥ 3.9
- Librerías necesarias listadas en `requirements.txt`

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

### Ejecución

Lanza la aplicación con:

```bash
python main.py
```

Se abrirá una interfaz gráfica donde puedes iniciar la interacción.

## Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación (GUI).
- `flows.py`: Organiza los flujos de interacción y llamadas a motores.
- `user_interaction_gui.py`: Interfaces para calificación y búsqueda de títulos.
- `recommendation_engine.py`: Calcula afinidad entre el perfil del usuario y cada plataforma.
- `user_profile.py`: Construye el perfil vectorial del usuario.
- `feature_engineering.py`: Vectoriza los contenidos con metadatos y TF-IDF.
- `nlp_utils.py`: Limpieza y normalización de texto.
- `data_utils.py`: Carga modelos TF-IDF y catálogos desde archivos.
- `tmdb_client.py` y `series_client.py`: Clientes para la API de TMDB.
- `config.py`: Parámetros de pesos y claves de API.

## Flujos Disponibles

1. **Películas**
2. **Series**
3. **Mixto**

Cada uno ofrece dos opciones:
- **Configuración rápida**: el sistema sugiere obras prediseñadas.
- **Configuración personalizada**: el usuario busca y califica libremente.

## Interacción del Usuario

- Puedes calificar títulos del 0.0 al 5.0.
- Se validan entradas erróneas (fuera de rango o no numéricas).
- La interfaz previene acciones inválidas y permite editar valoraciones.

El sistema sigue funcionando aunque solo se califiquen contenidos positivos. No requiere un balance entre puntuaciones altas y bajas: la ausencia de calificación no se interpreta como rechazo.

## Calibración de Pesos

Puedes modificar la importancia relativa de cada característica desde `config.py`, editando el diccionario `WEIGHTS`.

```python
WEIGHTS = {
    "genres": 1.5,
    "overview_tfidf": 1.0,
    ...
}
```

## Clave de API

La API de TMDB requiere clave. Añádela en `config.py`:

```python
TMDB_API_KEY = "TU_CLAVE_AQUI"
```

## Licencia

Este software está licenciado bajo los términos de la **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Puedes consultar el texto completo de la licencia en el archivo [`LICENSE`](./LICENSE) o en [https://www.gnu.org/licenses/agpl-3.0.html](https://www.gnu.org/licenses/agpl-3.0.html).
