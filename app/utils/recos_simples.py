from app.db.conector import get_connection
from app.rutas.mangas import encontrarManga
from app.core.config import get_settings


settings = get_settings()
STATIC_PORTADAS_BASE = settings.static_portadas_path.rstrip("/") or "/static"
DEFAULT_PORTADA_URL = f"{STATIC_PORTADAS_BASE}/{settings.default_portada_filename}"

conn = get_connection()

def cargar_mangas():
    query = """
    SELECT m.*, GROUP_CONCAT(g.nombre) AS generos
    FROM mangas m
    LEFT JOIN mangas_generos mg ON m.id = mg.id_manga
    LEFT JOIN generos g ON mg.id_genero = g.id
    GROUP BY m.id;
    """
    mangas = []
    #-: dividir los géneros en lista y normalizar
    for row in conn.execute(query):
        generos = [g.strip().lower() for g in row["generos"].split(",")] if row["generos"] else []
        mangas.append({
            "id": row["id"],
            "titulo": row["titulo"],
            "descripcion": row["descripcion"] or "",
            "tipo": row["tipo"],
            "url_portada": row["url_portada"] or DEFAULT_PORTADA_URL,
            "estado_publicacion": row["estado_publicacion"],
            "capitulos_totales": row["capitulos_totales"] or 0,
            "nota_general": row["nota_general"],
            "autor": row["autor"],
            "fecha_creacion": row["fecha_creacion"],
            "generos": generos
        })

    return mangas


def cargar_leidos(user_id):
    query = """
    SELECT id_manga
    FROM usuarios_mangas
    WHERE id_usuario = ? AND estado_lectura = 'favorito' AND ;
    """, (user_id)
    return [row["id_manga"] for row in conn.execute(query, (user_id,))]


def jaccard(a, b):
    # sacamos los generos de cada manga
    set_a = set(a)
    set_b = set(b)

    # la intersecion son son todos los generos posibles
    inter = len(set_a & set_b)

    # la union son los generos que comparten
    union = len(set_a | set_b)
    # si no compareten ninguno no ahi parentesco
    if union == 0:
        return 0
    
    # entonces el parentesco es el porcentaje que comparten (union)
    # entre el total de generos posibles (inter)
    return inter / union


def recomendar(user_id, top=5):
    mangas = cargar_mangas()
    leidos = cargar_leidos(user_id)

    #- AQUI ESTAMOS HACIENDO LAS MATRICES DE LOS MANGAS LEIDOS
    perfil_generos = []
    perfil_autores = []

    for m in mangas: 
        #- aqui comparamos solo el id porque es lo unico que hemos extraido
        if m["id"] in leidos:
            perfil_generos += [g.strip().lower() for g in m["generos"]]
            perfil_autores += (m["autor"].lower().strip())

    if not perfil_generos:  # -: si no hay favoritos, usamos todos los géneros
        for m in mangas:
            perfil_generos += [g.strip().lower() for g in m["generos"]]
            perfil_autores += (m["autor"].lower().strip())

    perfil_generos = list(set(perfil_generos))

    #- Calcular similitudes
    recomendaciones = []
    for m in mangas:
        if m["id"] not in leidos:
            #- aqui comparamos manga por manga con la matriz de nuestros gustos
            generos_manga = [g.strip().lower() for g in m["generos"]]
            score = jaccard(perfil_generos, generos_manga)
            if m["autor"] in perfil_autores:
                score *= 1.15
            recomendaciones.append((m, score))

    #- ordenamos por parentesco la lista de similitudes
    recomendaciones.sort(key=lambda x: x[1], reverse=True)
    #- AQUI DEVOLVEMOS SOLO LOS QUE HAYAMOS DICHO

    #- Creamos el return correctamente

    return recomendaciones[:top]
