from typing import List, Optional
import asyncio
from app.db.conector import get_connection
from app.models.manga import EstadoManga, TipoManga, MangaUpdate, MangaQuery, MangaBase
from fastapi import Form, File, UploadFile, HTTPException, APIRouter, Depends
import os, shutil
from app.rutas.usuarios import get_usuario_actual, get_usuario_actual_opcional
from app.core.config import get_settings

router = APIRouter()

settings = get_settings()
PORTADAS_DIR = settings.resources_portadas_dir
STATIC_PORTADAS_BASE = settings.static_portadas_path.rstrip("/") or "/static"
DEFAULT_PORTADA_URL = f"{STATIC_PORTADAS_BASE}/{settings.default_portada_filename}"


@router.post("/")
async def crear_manga(
    manga: MangaBase,
    user: dict = Depends(get_usuario_actual)
):
    if user["rol"] not in ("admin", "scan"):
        raise HTTPException(status_code=401, detail="no auntentificado")

    def _crear():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM mangas WHERE titulo = ?", (manga.titulo,))
            mangaTitulo = cursor.fetchone()
            if mangaTitulo:
                raise HTTPException(200, {"***manga ya existente***": dict(mangaTitulo)})

            url_portada = DEFAULT_PORTADA_URL

            cursor.execute(
                """
                INSERT INTO mangas (titulo, descripcion, tipo, estado_publicacion, autor, url_portada)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (manga.titulo, manga.descripcion, manga.tipo, manga.estado_publicacion, manga.autor, url_portada),
            )
            conn.commit()
            manga_id = cursor.lastrowid

            if manga.generos:
                for genero in manga.generos:
                    genero = genero.strip().lower()
                    cursor.execute("SELECT id FROM generos WHERE nombre = ?", (genero,))
                    genero_db = cursor.fetchone()

                    if genero_db:
                        genero_id = genero_db["id"]
                    else:
                        cursor.execute("INSERT INTO generos (nombre) VALUES (?)", (genero,))
                        conn.commit()
                        genero_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO mangas_generos (id_manga, id_genero) VALUES (?, ?)",
                        (manga_id, genero_id),
                    )
                conn.commit()

            cursor.execute("SELECT * FROM mangas WHERE id = ?", (manga_id,))
            manga_db = dict(cursor.fetchone())

            cursor.execute(
                """
                SELECT g.nombre 
                FROM generos g
                INNER JOIN mangas_generos mg ON g.id = mg.id_genero
                WHERE mg.id_manga = ?
                """,
                (manga_id,),
            )
            generos_db = []
            for row in cursor.fetchall():
                generos_db = row["nombre"]

            manga_db["generos"] = generos_db
            return manga_db
        finally:
            conn.close()

    return await asyncio.to_thread(_crear)




@router.get("/", response_model=List)
async def listar_mangas(
    manga: MangaQuery = Depends(),
    usuario_actual: Optional[dict] = Depends(get_usuario_actual_opcional)
):
    def _listar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if usuario_actual:
                query = """
                    SELECT DISTINCT m.*, 
                        um.estado_lectura,
                        um.puntuacion,
                        um.comentario_personal,
                        um.id_ultimo_capitulo_leido
                    FROM mangas m
                    LEFT JOIN mangas_generos mg ON m.id = mg.id_manga
                    LEFT JOIN generos g ON mg.id_genero = g.id
                    LEFT JOIN usuarios_mangas um ON (m.id = um.id_manga AND um.id_usuario = ?)
                    WHERE 1=1
                """
                params = [usuario_actual["id"]]
            else:
                query = """
                    SELECT DISTINCT m.* 
                    FROM mangas m
                    LEFT JOIN mangas_generos mg ON m.id = mg.id_manga
                    LEFT JOIN generos g ON mg.id_genero = g.id
                    WHERE 1=1
                """
                params = []

            if manga:
                if manga.titulo:
                    query += " AND m.titulo LIKE ?"
                    params.append(f"%{manga.titulo}%")
                if manga.tipo:
                    query += " AND m.tipo = ?"
                    params.append(manga.tipo)
                if manga.estado_publicacion:
                    query += " AND m.estado_publicacion = ?"
                    params.append(manga.estado_publicacion)
                if manga.generos:
                    query += " AND g.nombre LIKE ?"
                    params.append(f"%{manga.generos}%")
                if manga.autor:
                    query += " AND m.autor LIKE ?"
                    params.append(f"%{manga.autor}%")
                if manga.capitulos_totales:
                    query += " AND m.capitulos_totales <= ?"
                    params.append(manga.capitulos_totales)

            query += " ORDER BY m.nota_general DESC"

            cursor.execute(query, params)
            mangas = cursor.fetchall()

            resultado = []
            for fila_manga in mangas:
                manga_dict = dict(fila_manga)
                cursor.execute(
                    """
                    SELECT g.nombre 
                    FROM generos g
                    INNER JOIN mangas_generos mg ON g.id = mg.id_genero
                    WHERE mg.id_manga = ?
                    """,
                    (manga_dict["id"],),
                )
                generos = [row["nombre"] for row in cursor.fetchall()]
                manga_dict["generos"] = generos

                if usuario_actual:
                    manga_dict["en_mi_lista"] = manga_dict.get("estado_lectura") is not None
                    manga_dict["mi_estado"] = manga_dict.get("estado_lectura")
                    manga_dict["mi_puntuacion"] = manga_dict.get("puntuacion")
                    manga_dict["mi_comentario"] = manga_dict.get("comentario_personal")
                    manga_dict["ultimo_capitulo_leido"] = manga_dict.get("id_ultimo_capitulo_leido")

                    for campo in [
                        "estado_lectura",
                        "puntuacion",
                        "comentario_personal",
                        "id_ultimo_capitulo_leido",
                    ]:
                        manga_dict.pop(campo, None)

                resultado.append(manga_dict)

            return resultado
        finally:
            conn.close()

    return await asyncio.to_thread(_listar)

@router.get("/{id}")
async def encontrarManga(id: int, user=Depends(get_usuario_actual_opcional)):
    def _encontrar():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM mangas WHERE id = ?", (id,))
        manga = cursor.fetchone()
        if not manga:
            conn.close()
            return {"error": "Manga no encontrado"}
        manga_dict = dict(manga)

        cursor.execute(
            """
            SELECT g.nombre
            FROM generos g
            INNER JOIN mangas_generos mg ON g.id = mg.id_genero
            WHERE mg.id_manga = ?
            """,
            (id,),
        )
        generos = [row["nombre"] for row in cursor.fetchall()]
        manga_dict["generos"] = generos

        cursor.execute(
            """
            SELECT id, titulo, numero
            FROM capitulos
            WHERE id_manga = ?
            ORDER BY numero ASC
            """,
            (id,),
        )
        capitulos = [dict(row) for row in cursor.fetchall()]
        manga_dict["capitulos"] = capitulos

        if user:
            cursor.execute(
                """
                SELECT estado_lectura, puntuacion, comentario_personal, id_ultimo_capitulo_leido
                FROM usuarios_mangas
                WHERE id_usuario = ? AND id_manga = ?
                """,
                (user["id"], id),
            )
            personal = cursor.fetchone()
            manga_dict["personal"] = dict(personal) if personal else None

        conn.close()
        return manga_dict

    return await asyncio.to_thread(_encontrar)




@router.get("/{manga_id}/capitulos")
async def listar_capitulos(manga_id: int):
    def _listar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM capitulos WHERE id_manga = ? ORDER BY numero",
                (manga_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    return await asyncio.to_thread(_listar)


@router.put("/{manga_id}")
async def actualizar_manga(
    manga_id: int,
    datos: MangaUpdate,
    usuario_actual: dict = Depends(get_usuario_actual)
):
    if usuario_actual["rol"] not in ("admin", "scan"):
        raise HTTPException(status_code=401, detail="No estás autorizado para modificar mangas")

    def _actualizar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM mangas WHERE id = ?", (manga_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Manga no encontrado")

            if datos.generos is not None:
                cursor.execute("DELETE FROM mangas_generos WHERE id_manga = ?", (manga_id,))
                for genero in datos.generos:
                    cursor.execute("SELECT id FROM generos WHERE nombre = ?", (genero,))
                    fila_genero = cursor.fetchone()
                    if not fila_genero:
                        cursor.execute("INSERT INTO generos (nombre) VALUES (?)", (genero,))
                        id_genero = cursor.lastrowid
                    else:
                        id_genero = fila_genero[0]

                    cursor.execute(
                        "INSERT INTO mangas_generos (id_manga, id_genero) VALUES (?, ?)",
                        (manga_id, id_genero)
                    )

            campos = []
            valores = []
            for campo, valor in datos.dict(exclude_unset=True, exclude={"generos"}).items():
                campos.append(f"{campo} = ?")
                valores.append(valor)

            if campos:
                valores.append(manga_id)
                query = f"UPDATE mangas SET {', '.join(campos)} WHERE id = ?"
                cursor.execute(query, tuple(valores))

            conn.commit()

            cursor.execute(
                """
                SELECT id, titulo, descripcion, tipo, url_portada, estado_publicacion, 
                    capitulos_totales, nota_general, autor 
                FROM mangas 
                WHERE id = ?
                """,
                (manga_id,),
            )
            fila = cursor.fetchone()

            cursor.execute(
                """
                SELECT g.nombre 
                FROM generos g
                JOIN mangas_generos mg ON g.id = mg.id_genero
                WHERE mg.id_manga = ?
                """,
                (manga_id,),
            )
            generos = [row[0] for row in cursor.fetchall()]

            return {
                "id": fila[0],
                "titulo": fila[1],
                "descripcion": fila[2],
                "tipo": fila[3],
                "estado_publicacion": fila[5],
                "capitulos_totales": fila[6],
                "nota_general": float(fila[7]) if fila[7] is not None else None,
                "autor": fila[8],
                "generos": generos
            }
        finally:
            conn.close()

    return await asyncio.to_thread(_actualizar)


@router.put("/{id_manga}/portada")
async def actualizar_portada(
    id_manga: int,
    portada: UploadFile = File(...),
    usuario = Depends(get_usuario_actual)
):
    if usuario["rol"] not in ("admin", "scan"):
        raise HTTPException(status_code=401, detail="No autenticado")

    def _actualizar_portada():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM mangas WHERE id = ?", (id_manga,))
            manga = cursor.fetchone()
            if not manga:
                raise HTTPException(status_code=404, detail="Manga no encontrado")

            carpeta_portadas = PORTADAS_DIR
            os.makedirs(carpeta_portadas, exist_ok=True)

            
            mapa_mime = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
            }
            # los mime son la informacion que nos da el navegador 
            # sobre el tipo de archivo que estamos subiendo
            # asique si el archivo no tiene una extension valida la intentamos obtener del mime
            extensiones_permitidas = {".jpg", ".jpeg", ".png", ".webp"}

            extension = os.path.splitext(portada.filename or "")[1].lower()
            content_type = (portada.content_type or "").lower()
            if extension not in extensiones_permitidas:
                # si el archivo no tiene una extension valida la intentamos obtener del mime
                extension = mapa_mime.get(content_type, ".jpg")

            rutas_existentes = [
                # aqui creamos la ruta de la portada con cada extension permitida
                # esto es para eliminar las portadas anteriores aun con otras extensiones
                os.path.join(carpeta_portadas, f"{id_manga}{ext}")
                for ext in extensiones_permitidas
            ]
            # aqui creamos la ruta de la portada sin extension
            rutas_existentes.append(os.path.join(carpeta_portadas, str(id_manga)))

            for ruta in rutas_existentes:
                # si la ruta existe la eliminamos
                if os.path.exists(ruta):
                    os.remove(ruta)

            ruta_archivo = os.path.join(carpeta_portadas, f"{id_manga}{extension}")
            portada.file.seek(0)
            with open(ruta_archivo, "wb") as buffer:
                shutil.copyfileobj(portada.file, buffer)

            ruta_portada = f"{STATIC_PORTADAS_BASE}/{id_manga}{extension}"

            cursor.execute("UPDATE mangas SET url_portada = ? WHERE id = ?", (ruta_portada, id_manga))
            conn.commit()
            return {"id": id_manga, "url_portada": ruta_portada}
        finally:
            conn.close()

    return await asyncio.to_thread(_actualizar_portada)
