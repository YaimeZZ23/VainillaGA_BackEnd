from typing import List
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

from app.core.config import get_settings


settings = get_settings()


def verificar_imagenes(archivos: List[UploadFile]):
    """
    Verifica que todos los archivos subidos sean imágenes válidas.
    Lanza HTTPException si alguno no lo es.
    """
    for archivo in archivos:
        contenido = archivo.file.read()

        if len(contenido) < settings.min_image_bytes:
            archivo.file.seek(0)
            raise HTTPException(
                status_code=400,
                detail=f"El archivo '{archivo.filename}' pesa menos de {settings.min_image_bytes} bytes"
            )

        try:
            Image.open(io.BytesIO(contenido))
        except Exception:
            archivo.file.seek(0)
            raise HTTPException(
                status_code=400,
                detail=f"El archivo '{archivo.filename}' no es una imagen válida"
            )

        archivo.file.seek(0)

def verificar_formato(imagenes: list[str]):

    formatos_validos = ["webp", "avif", "jpg", "png", "svg", "jpeg"]

    for pagina in imagenes:
        partes = pagina.split(".")
        if partes[-1] not in formatos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"La imagen '{pagina}' no es una imagen válida"
            )