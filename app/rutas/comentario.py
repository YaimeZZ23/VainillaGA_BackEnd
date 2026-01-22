from fastapi import APIRouter, HTTPException, Form, Depends
from typing import Optional
import asyncio
from app.db.conector import get_connection
from app.rutas.usuarios import get_usuario_actual


router = APIRouter()


@router.post("/{manga_id}")
async def crear_comentario(
    manga_id: int,
    texto: str,
    id_comentario_padre: Optional[int] = None,
    usuario_actual: dict = Depends(get_usuario_actual),
):
    def _crear():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO comentarios (id_usuario, id_manga, texto, id_comentario_padre, likes)
                VALUES (?, ?, ?, ?, 0)
                """,
                (usuario_actual["id"], manga_id, texto, id_comentario_padre),
            )
            conn.commit()
            comentario_id = cursor.lastrowid
            cursor.execute("SELECT * FROM comentarios WHERE id = ?", (comentario_id,))
            comentario_db = cursor.fetchone()
            return dict(comentario_db)
        finally:
            conn.close()

    return await asyncio.to_thread(_crear)


@router.get("/{manga_id}")
async def listar_comentarios(manga_id: int):
    def _listar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT c.id, c.texto, c.id_comentario_padre, c.likes, c.fecha_creacion,
                u.id AS id_usuario, u.nombre_usuario
                FROM comentarios c
                JOIN usuarios u ON c.id_usuario = u.id
                WHERE c.id_manga = ?
                ORDER BY c.fecha_creacion ASC
                """,
                (manga_id,),
            )
            comentarios = cursor.fetchall()
            return [dict(comentario) for comentario in comentarios]
        finally:
            conn.close()

    return await asyncio.to_thread(_listar)



@router.delete("/{comentario_id}")
async def borrar_comentario(
    comentario_id: int,
    usuario_actual: dict = Depends(get_usuario_actual),
):
    def _borrar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM comentarios WHERE id = ?", (comentario_id,))
            comentario = cursor.fetchone()
            if not comentario:
                raise HTTPException(404, "Comentario no encontrado")
            if comentario["id_usuario"] != usuario_actual["id"] and usuario_actual["rol"] != "admin":
                raise HTTPException(401, "No autorizado")
            cursor.execute("DELETE FROM comentarios WHERE id = ?", (comentario_id,))
            conn.commit()
            return {"detalle": "Comentario borrado"}
        finally:
            conn.close()

    return await asyncio.to_thread(_borrar)


@router.put("/{comentario_id}/like")
async def like_comentario(
    comentario_id: int,
    usuario_actual: dict = Depends(get_usuario_actual),
):
    def _like():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM comentarios WHERE id = ?", (comentario_id,))
            comentario = cursor.fetchone()
            if not comentario:
                raise HTTPException(404, "Comentario no encontrado")

            cursor.execute(
                "SELECT 1 FROM comentarios_likes WHERE id_usuario = ? AND id_comentario = ?",
                (usuario_actual["id"], comentario_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Ya has dado like a este comentario")

            cursor.execute(
                "INSERT INTO comentarios_likes (id_usuario, id_comentario) VALUES (?, ?)",
                (usuario_actual["id"], comentario_id),
            )

            cursor.execute("UPDATE comentarios SET likes = likes + 1 WHERE id = ?", (comentario_id,))
            conn.commit()
            return {"detalle": "Like agregado"}
        finally:
            conn.close()

    return await asyncio.to_thread(_like)