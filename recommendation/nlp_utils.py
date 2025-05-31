# recommendation/nlp_utils.py

"""
Utilidades de procesamiento de lenguaje natural para limpiar y normalizar
el texto de overviews de películas y series antes de la vectorización.
"""

import re
import nltk
from nltk.corpus import stopwords

# Descargamos las stopwords de NLTK en inglés
nltk.download('stopwords', quiet=True)

# Conjunto de palabras vacías esenciales en inglés
ESSENTIAL_STOP = set(stopwords.words('english'))

def clean_overview(text: str) -> str:
    """
    Limpia y normaliza el texto de la sinopsis de la película/serie:
      - Convierte todo el texto a minúsculas
      - Elimina enlaces web (http, www)
      - Reemplaza caracteres no alfabéticos por espacios
      - Tokeniza y filtra palabras vacías y tokens muy cortos (<= 2 caracteres)

    Parámetros:
    - text: cadena de texto original (overview)

    Retorna:
    - Cadena de texto limpia y preparada para vectorización TF-IDF
    """
    # Si la entrada no es de tipo string, devolvemos el texto vacío para evitar errores
    if not isinstance(text, str):
        return ""

    # 1) Pasamos a minúsculas para normalizar
    text = text.lower()

    # 2) Eliminamos URLs (cualquier http... o www....)
    text = re.sub(r'http\S+|www\.\S+', '', text)

    # 3) Reemplazamos todo lo que no sea letra (a-z) o espacio por espacio
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 4) Tokenizamos y filtramos stopwords esenciales y tokens muy cortos
    tokens = [w for w in text.split() if w not in ESSENTIAL_STOP and len(w) > 2]

    # 5) Reconstruimos la cadena limpia
    return " ".join(tokens)
