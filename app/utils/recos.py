from contextlib import closing
from typing import Dict, List, Tuple, Optional

import asyncio

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse import diags
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer
from sklearn.preprocessing import normalize

from app.db.conector import get_connection
from app.utils.stop_words import stop_words_spanish
from app.core.config import get_settings


settings = get_settings()
STATIC_PORTADAS_BASE = settings.static_portadas_path.rstrip("/") or "/static"
DEFAULT_PORTADA_URL = f"{STATIC_PORTADAS_BASE}/{settings.default_portada_filename}"

MAX_TOP_RESULTS = 50


# ==========================================================
# 1. Obtener y preparar los datos base
# ==========================================================

#   Paso 1: Traemos el catálogo bruto desde la base de datos.

#   Separar este paso nos permite diferenciar claramente la capa de datos de
#   la capa de machine learning, una práctica esencial al aprender o crear
#   sistemas productivos.

def cargar_mangas(conn) -> pd.DataFrame:
    

    query = """
    SELECT m.id,
        m.titulo,
        m.descripcion,
        m.tipo,
        m.autor,
        m.estado_publicacion,
        m.capitulos_totales,
        m.nota_general,
        GROUP_CONCAT(g.nombre) AS generos,
        m.url_portada
    FROM mangas m
    LEFT JOIN mangas_generos mg ON m.id = mg.id_manga
    LEFT JOIN generos g ON mg.id_genero = g.id
    GROUP BY m.id;
    """

    catalogo = pd.read_sql(query, conn)

    # Limpiamos valores faltantes para que los transformadores funcionen sin errores.
    catalogo["descripcion"] = catalogo["descripcion"].fillna("")
    catalogo["generos"] = catalogo["generos"].fillna("")
    catalogo["generos_lista"] = catalogo["generos"].apply(lambda raw: raw.split(",") if raw else [])
    catalogo["nota_general"] = catalogo["nota_general"].fillna(0.0)
    catalogo["capitulos_totales"] = catalogo["capitulos_totales"].fillna(0.0)
    catalogo["url_portada"] = catalogo["url_portada"].fillna(DEFAULT_PORTADA_URL)
    catalogo["autor"] = catalogo["autor"].fillna("Autor desconocido")
    catalogo["estado_publicacion"] = catalogo["estado_publicacion"].fillna("desconocido")

    catalogo = catalogo.reset_index(drop=True)
    catalogo["id"] = catalogo["id"].astype(int)
    catalogo["tipo"] = catalogo["tipo"].fillna("desconocido")

    return catalogo

#   Paso 2: Sacamos los mangas de la lista de favoritos del usuario y su puntuación
def cargar_historial(conn, user_id: int) -> pd.DataFrame:

    query = """
    SELECT id_manga,
        puntuacion,
        estado_lectura
    FROM usuarios_mangas
    WHERE id_usuario = ?;
    """

    historial = pd.read_sql(query, conn, params=(user_id,))

    if historial.empty:
        return historial

    historial["puntuacion"] = historial["puntuacion"].fillna(0.0)
    historial["estado_lectura"] = historial["estado_lectura"].fillna("").str.lower()
    historial["id_manga"] = historial["id_manga"].astype(int)

    return historial


# ==========================================================
# 2. Representar el catálogo en forma de vectores
# ==========================================================
def construir_representacion_contenido(catalogo: pd.DataFrame) -> Tuple[sparse.csr_matrix, sparse.csr_matrix, Dict[int, int]]:
    #   Paso 3: Convertimos cada manga en un vector numérico.

    """Aquí aplicamos dos ideas muy comunes en ML:
    1. **TF-IDF** para texto: destaca palabras relevantes de las descripciones.
    2. **Multi Label Binarizer + MinMaxScaler** para convertir categorías/listas y
    números en valores comparables.

    El resultado son dos matrices:
    - `X_weighted`: combinación ponderada de todas las características (para promediar gustos).
    - `X_normalized`: la misma matriz pero normalizada fila a fila para usar
    similitud coseno de forma directa.
    """

    # 2.1 Texto -> TF-IDF
    vectorizador_tfidf = TfidfVectorizer(max_features=2000, stop_words=stop_words_spanish)
    X_desc = vectorizador_tfidf.fit_transform(catalogo["descripcion"])

    # 2.2 Géneros -> vector multietiqueta (uno por cada género posible)
    binarizador_generos = MultiLabelBinarizer()
    X_gen = sparse.csr_matrix(binarizador_generos.fit_transform(catalogo["generos_lista"]))

    # 2.3 Variables numéricas -> escalado Min-Max (entre 0 y 1)
    escalador = MinMaxScaler()
    X_nota_caps = sparse.csr_matrix(escalador.fit_transform(
        catalogo[["nota_general", "capitulos_totales"]]
    ))

    # 2.4 Unimos todos los bloques de características en una sola matriz dispersa.
    X = sparse.hstack([X_desc, X_gen, X_nota_caps], format="csr")

    # 2.5 Asignamos pesos manuales (heurísticos) a cada bloque para explicar su importancia.
    pesos_bloques = {
        "descripcion": 0.6,
        "generos": 2.0,
        "numericas": 1.2,
    }

    weights = np.concatenate([
        np.full(X_desc.shape[1], pesos_bloques["descripcion"]),
        np.full(X_gen.shape[1], pesos_bloques["generos"]),
        np.full(X_nota_caps.shape[1], pesos_bloques["numericas"]),
    ])

    X_weighted = X.dot(diags(weights))
    X_normalized = normalize(X_weighted, axis=1)

    # Mapeo útil para enlazar ids de mangas con filas de la matriz.
    id_a_indice = {int(manga_id): idx for idx, manga_id in enumerate(catalogo["id"].tolist())}

    return X_normalized, X_weighted, id_a_indice


# ==========================================================
# 3. Aprender el perfil del usuario
# ==========================================================
def construir_perfil_usuario(
    historial: pd.DataFrame,
    id_a_indice: Dict[int, int],
    X_weighted: sparse.csr_matrix,
) -> Optional[sparse.csr_matrix]:
    """Paso 4: Resumimos los gustos del usuario en un vector promedio ponderado.

    Cada manga leído aporta su vector, ponderado por señales simples:
    - La puntuación explícita (si existe).
    - Si marcó el manga como "favorito".
    El resultado es el vector (`perfil`) que usaremos para buscar títulos similares.
    """

    if historial.empty:
        return None

    indices = []
    pesos = []

    for _, fila in historial.iterrows():
        idx = id_a_indice.get(int(fila["id_manga"]))
        if idx is None:
            continue

        puntuacion = float(fila.get("puntuacion", 0.0))
        peso = 1.0 + (puntuacion / 10.0 if puntuacion > 0 else 0.0)

        estado = str(fila.get("estado_lectura", "")).strip().lower()
        if estado == "favorito":
            peso += 1.0

        indices.append(idx)
        pesos.append(peso)

    if not indices or np.sum(pesos) == 0:
        return None

    vectores_usuario = X_weighted[indices, :]
    pesos = np.array(pesos)
    perfil = sparse.csr_matrix(pesos).dot(vectores_usuario) / pesos.sum()

    return normalize(perfil, axis=1)


# ==========================================================
# 4. Calcular la similitud y preparar la respuesta
# ==========================================================
def calcular_similitud(perfil: Optional[sparse.csr_matrix], X_normalized: sparse.csr_matrix) -> np.ndarray:
    """Paso 5: Medimos similitud coseno entre el perfil y todo el catálogo.

    Si el usuario no tiene historial suficiente devolvemos un vector de ceros
    para indicar que no hay preferencias aprendidas todavía.
    """

    if perfil is None:
        return np.zeros(X_normalized.shape[0])

    return X_normalized.dot(perfil.T).toarray().ravel()


def preparar_recomendaciones(
    catalogo: pd.DataFrame,
    historial: pd.DataFrame,
    scores: np.ndarray,
    top: int,
) -> List[Dict[str, object]]:
    """Paso 6: Ordenamos los candidatos y los dejamos listos para la API."""

    vistos = set(historial["id_manga"].tolist()) if not historial.empty else set()
    mask = ~catalogo["id"].isin(vistos)
    candidatos = catalogo.loc[mask].copy()

    if scores.sum() == 0:
        # Estrategia de respaldo: ordenar por la nota general cuando no hay perfil.
        candidatos["score"] = candidatos["nota_general"].astype(float)
    else:
        candidatos["score"] = scores[mask.values]

    candidatos["score"] = np.nan_to_num(candidatos["score"], nan=0.0, posinf=0.0, neginf=0.0)

    seleccion = candidatos.sort_values("score", ascending=False).head(top)

    resultados: List[Dict[str, object]] = []
    for _, fila in seleccion.iterrows():
        item: Dict[str, object] = {}
        for columna, valor in fila.items():
            if isinstance(valor, (np.generic,)):
                valor = valor.item()
            if isinstance(valor, float) and (np.isnan(valor) or np.isinf(valor)):
                valor = 0.0
            item[columna] = valor

        item.setdefault("generos_lista", [])
        # Garantizamos que la clave generos (usada por el front) sea una lista real.
        item["generos"] = list(item.get("generos_lista", []))
        resultados.append(item)

    return resultados


# ==========================================================
# 5. Función de alto nivel que une todos los pasos
# ==========================================================
async def recomendar(user_id: int, top: int = 5) -> List[Dict[str, object]]:
    """Genera recomendaciones usando el pipeline paso a paso descrito arriba."""

    if top <= 0:
        return []

    top = min(top, MAX_TOP_RESULTS)

    def _ejecutar_pipeline() -> List[Dict[str, object]]:
        with closing(get_connection()) as conn:
            catalogo = cargar_mangas(conn)
            historial = cargar_historial(conn, user_id)

        if catalogo.empty:
            return []

        X_normalized, X_weighted, id_a_indice = construir_representacion_contenido(catalogo)
        perfil = construir_perfil_usuario(historial, id_a_indice, X_weighted)
        scores = calcular_similitud(perfil, X_normalized)

        return preparar_recomendaciones(catalogo, historial, scores, top)

    return await asyncio.to_thread(_ejecutar_pipeline)
