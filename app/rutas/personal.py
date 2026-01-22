from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import asyncio
from app.rutas.usuarios import get_usuario_actual
from app.db.conector import get_connection
#from app.utils.recos_simples import recomendar
from app.models.manga import MangaUpdatePersonal
from app.utils.recos import recomendar
from app.utils.puntuacion_general import sacar_nota_media

router = APIRouter()

@router.get("/")
async def mis_mangas(usuario_actual: dict = Depends(get_usuario_actual)):
    def _mis_mangas():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                m.id, m.titulo, m.descripcion, m.tipo, m.url_portada, 
                m.estado_publicacion, m.capitulos_totales, m.nota_general, 
                m.autor, m.fecha_creacion, m.fecha_actualizacion, m.Ecchi,
                um.estado_lectura, um.puntuacion, um.comentario_personal, um.id_ultimo_capitulo_leido
            FROM mangas m
            LEFT JOIN usuarios_mangas um 
                ON m.id = um.id_manga AND um.id_usuario = ?
            ORDER BY um.fecha_actualizacion DESC
            """,
            (usuario_actual["id"],),
        )

        mangas_raw = cursor.fetchall()

        mangas = []
        for row in mangas_raw:
            row_dict = dict(row)

            cursor.execute(
                """
                SELECT g.nombre
                FROM generos g
                JOIN mangas_generos mg ON g.id = mg.id_genero
                WHERE mg.id_manga = ?
                """,
                (row_dict["id"],),
            )
            generos = [g["nombre"] for g in cursor.fetchall()]

            manga_obj = {
                "id": row_dict["id"],
                "titulo": row_dict["titulo"],
                "descripcion": row_dict["descripcion"],
                "tipo": row_dict["tipo"],
                "url_portada": row_dict["url_portada"],
                "estado_publicacion": row_dict["estado_publicacion"],
                "capitulos_totales": row_dict["capitulos_totales"],
                "nota_general": row_dict["nota_general"],
                "autor": row_dict["autor"],
                "fecha_creacion": row_dict["fecha_creacion"],
                "fecha_actualizacion": row_dict["fecha_actualizacion"],
                "Ecchi": row_dict["Ecchi"],
                "generos": generos,
                "en_mi_lista": row_dict["estado_lectura"] is not None,
                "mi_estado": row_dict["estado_lectura"],
                "mi_puntuacion": row_dict["puntuacion"],
                "mi_comentario": row_dict["comentario_personal"],
                "id_ultimo_capitulo_leido": row_dict["id_ultimo_capitulo_leido"],
            }

            mangas.append(manga_obj)

        conn.close()
        return mangas

    return await asyncio.to_thread(_mis_mangas)



#esta funcion al estar ejecutando calcular nota media a cada rato que es asyncrona
# para no tener que esperar a que termine cada vez que se actualiza un manga
# tenemos que hacer nosotros un await en esta funcion tambien
@router.put("/{id_manga}")
async def actualizar_manga_usuario(
    id_manga: int,
    manga: MangaUpdatePersonal,
    usuario_actual: dict = Depends(get_usuario_actual),
):
# esta es una funcion interna del endpoint, que se encarga de actualizar el manga
    def actualizar():
        conn = get_connection()
        cursor = conn.cursor()

        campos = []
        valores = []
        recalcular_nota = False
        if manga.estado_lectura:
            campos.append("estado_lectura = ?")
            valores.append(manga.estado_lectura)
        if manga.puntuacion:
            campos.append("puntuacion = ?")
            valores.append(manga.puntuacion)
            # si se actualiza la puntuacion, se recalculara la nota general
            recalcular_nota = True
        if manga.comentario_personal:
            campos.append("comentario_personal = ?")
            valores.append(manga.comentario_personal)
        if manga.id_ultimo_capitulo_leido:
            campos.append("id_ultimo_capitulo_leido = ?")
            valores.append(manga.id_ultimo_capitulo_leido)

        if not campos:
            conn.close()
            raise HTTPException(400, "No se enviaron datos para actualizar")
        valores.append(usuario_actual["id"])
        valores.append(id_manga)
        query = (
            f"UPDATE usuarios_mangas SET {', '.join(campos)}, fecha_actualizacion = CURRENT_TIMESTAMP "
            "WHERE id_usuario = ? AND id_manga = ?"
        )
        cursor.execute(query, valores)
        conn.commit()
        cursor.execute(
            "SELECT * FROM usuarios_mangas WHERE id_usuario = ? AND id_manga = ?",
            (usuario_actual["id"], id_manga),
        )
        manga_db = cursor.fetchone()
        conn.close()
        if not manga_db:
            return "error, revisa si el manga esta en leidos", False
        return manga_db, recalcular_nota
# este es el verdadero cuerpo del endpoint
# aqui se llama a la funcion interna y se espera a que termine
# si recalcular es True, se llama a la funcion de calcular nota media
# Aunque todo esto tampoco es de mucha utilidad ya que todo es un mismo programa
# pero es para que se pueda usar la funcion de calcular nota media desde otro endpoint
    manga_actualizado, recalcular = await asyncio.to_thread(actualizar)
    if recalcular:
        await sacar_nota_media()
    return manga_actualizado


@router.post("/{manga_id}")
async def agregar_manga_a_lista(
    manga_id: int,
    estado_lectura: str = "pendiente",
    usuario_actual: dict = Depends(get_usuario_actual),
):
    def _agregar():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM mangas WHERE id = ?", (manga_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Manga no encontrado")

        estados_validos = ["leyendo", "completado", "pendiente", "abandonado", "favorito"]
        if estado_lectura not in estados_validos:
            conn.close()
            raise HTTPException(status_code=400, detail="Estado de lectura inválido")

        try:
            cursor.execute(
                """
                INSERT INTO usuarios_mangas (id_usuario, id_manga, estado_lectura)
                VALUES (?, ?, ?)
                """,
                (usuario_actual["id"], manga_id, estado_lectura),
            )
            conn.commit()
            mensaje = "Manga agregado a tu lista"
        except Exception:
            cursor.execute(
                """
                UPDATE usuarios_mangas 
                SET estado_lectura = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id_usuario = ? AND id_manga = ?
                """,
                (estado_lectura, usuario_actual["id"], manga_id),
            )
            conn.commit()
            mensaje = "Estado del manga actualizado"

        cursor.execute(
            """
            SELECT um.*, m.titulo
            FROM usuarios_mangas um
            JOIN mangas m ON um.id_manga = m.id
            WHERE um.id_usuario = ? AND um.id_manga = ?
            """,
            (usuario_actual["id"], manga_id),
        )

        resultado = dict(cursor.fetchone())
        conn.close()

        return {"mensaje": mensaje, "manga": resultado}

    return await asyncio.to_thread(_agregar)

@router.delete("/{manga_id}")
async def quitar_manga_de_lista(
    manga_id: int,
    usuario_actual: dict = Depends(get_usuario_actual),
):
    """Quitar un manga de la lista personal del usuario"""

    def _quitar():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM usuarios_mangas 
            WHERE id_usuario = ? AND id_manga = ?
            """,
            (usuario_actual["id"], manga_id),
        )

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Manga no encontrado en tu lista")

        conn.commit()
        conn.close()

        return {"mensaje": "Manga eliminado de tu lista"}

    return await asyncio.to_thread(_quitar)

@router.get("/recomendaciones")
async def recomendar_mangas(
    cantidad: int = 5,
    usuario_actual: dict = Depends(get_usuario_actual),
):
    return await recomendar(usuario_actual["id"], cantidad)
