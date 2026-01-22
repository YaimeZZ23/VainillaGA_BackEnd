from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
import os, shutil
import asyncio
from app.db.conector import get_connection
import zipfile
from app.utils.file_service import verificar_imagenes
from app.rutas.usuarios import get_usuario_actual, get_usuario_actual_opcional
from app.core.config import get_settings

router = APIRouter()

settings = get_settings()
CAPITULOS_DIR = settings.resources_capitulos_dir
TMP_DIR = settings.resources_tmp_dir
STATIC_CAPITULOS_BASE = settings.static_capitulos_path.rstrip("/") or "/static"


@router.get("/{id_manga}")
async def listar_capitulos(id_manga: int):
    def _listar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM capitulos WHERE id_manga = ? ORDER BY numero", (id_manga,))
            capitulos = cursor.fetchall()
            return [dict(c) for c in capitulos]
        finally:
            conn.close()

    return await asyncio.to_thread(_listar)


@router.get("/{id_capitulo}/manga/{id_manga}")
async def obtener_paginas(id_manga: int, id_capitulo: int, usuario = Depends(get_usuario_actual_opcional)):
    def _obtener():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT p.numero, p.url_pagina
                FROM paginas p
                JOIN capitulos c ON p.id_capitulo = c.id
                WHERE c.id_manga = ? AND c.id = ?
                ORDER BY p.numero ASC
                """,
                (id_manga, id_capitulo),
            )

            paginas = cursor.fetchall()

            if not paginas:
                raise HTTPException(status_code=404, detail="Capítulo o páginas no encontradas")

            if usuario:
                cursor.execute(
                    """
                    UPDATE usuarios_mangas
                    SET id_ultimo_capitulo_leido = ?
                    WHERE id_usuario = ? AND id_manga = ?;
                    """,
                    (id_capitulo, usuario["id"], id_manga),
                )

                conn.commit()

            resultado = {
                "id_manga": id_manga,
                "id_capitulo": id_capitulo,
                "paginas": [],
            }

            for p in paginas:
                resultado["paginas"].append({
                    "numero": p["numero"],
                    "url": p['url_pagina']
                })

            return resultado
        finally:
            conn.close()

    return await asyncio.to_thread(_obtener)



@router.post("/{manga_id}")
async def subir_capitulo(
    manga_id: int,
    titulo: str = Form(None),
    numero: int = Form(...),
    zip_file: UploadFile = File(...),
    cliente = Depends(get_usuario_actual)
):
    if cliente["rol"] not in ("admin", "scan"):
        raise HTTPException(status_code=401, detail="No estás autorizado para modificar mangas")

    def _subir():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM mangas WHERE id = ?", (manga_id,))
            manga_db = cursor.fetchone()
            if not manga_db:
                raise HTTPException(404, "Manga no encontrado")

            cursor.execute("SELECT * FROM capitulos WHERE numero = ? and id_manga = ?", (numero, manga_id))
            capitulo = cursor.fetchone()
            if capitulo:
                raise HTTPException(404, "Capitulo ya existente")

            os.makedirs(TMP_DIR, exist_ok=True)
            temp_zip_path = os.path.join(TMP_DIR, zip_file.filename)
            with open(temp_zip_path, "wb") as buffer:
                shutil.copyfileobj(zip_file.file, buffer)

            chapter_path = os.path.join(
                CAPITULOS_DIR,
                f"manga_{manga_id}",
                f"capitulo_{numero}"
            )
            os.makedirs(chapter_path, exist_ok=True)

            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                zip_ref.extractall(chapter_path)

            archivos = []
            for filename in os.listdir(chapter_path):
                filepath = os.path.join(chapter_path, filename)
                archivos.append(UploadFile(filename=filename, file=open(filepath, "rb")))

            try:
                verificar_imagenes(archivos)
            except HTTPException as e:
                shutil.rmtree(chapter_path, ignore_errors=True)
                os.remove(temp_zip_path)
                raise e
            finally:
                for a in archivos:
                    a.file.close()

            os.remove(temp_zip_path)

            cursor.execute(
                "INSERT INTO capitulos (id_manga, numero, titulo) VALUES (?, ?, ?)",
                (manga_id, numero, titulo)
            )
            conn.commit()
            capitulo_id = cursor.lastrowid

            cursor.execute(
                """UPDATE mangas SET capitulos_totales = capitulos_totales + 1, 
                                fecha_actualizacion = CURRENT_DATE WHERE id = ?""",
                (manga_id,),
            )
            conn.commit()

            paginas = sorted(os.listdir(chapter_path))
            for idx, pagina in enumerate(paginas, start=1):
                url_pagina = f"{STATIC_CAPITULOS_BASE}/manga_{manga_id}/capitulo_{numero}/{pagina}"
                cursor.execute(
                    "INSERT INTO paginas (id_capitulo, numero, url_pagina) VALUES (?, ?, ?)",
                    (capitulo_id, idx, url_pagina),
                )
            conn.commit()

            cursor.execute("SELECT * FROM capitulos WHERE id = ?", (capitulo_id,))
            capitulo_db = dict(cursor.fetchone())

            cursor.execute(
                "SELECT numero, url_pagina FROM paginas WHERE id_capitulo = ? ORDER BY numero",
                (capitulo_id,),
            )
            capitulo_db["paginas"] = [dict(row) for row in cursor.fetchall()]

            return capitulo_db
        finally:
            conn.close()

    return await asyncio.to_thread(_subir)
