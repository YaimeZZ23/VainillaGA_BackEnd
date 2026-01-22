from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import base64
from app.db.init_db import init_db
from app.rutas import auth, mangas, capitulos, usuarios, comentario, personal
from app.utils.puntuacion_general import sacar_nota_media
from fastapi.middleware.cors import CORSMiddleware #esto es para evitar que se bloque por cors, basicamente
#lo que hacen los navegadores para evitar que una web haga peticiones a otra web sin permiso con fests raros
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title="Manga API")


def asegurar_portada_por_defecto():
    carpeta_portadas = Path(settings.resources_portadas_dir)
    carpeta_portadas.mkdir(parents=True, exist_ok=True)
    ruta_portada = carpeta_portadas / settings.default_portada_filename
    if ruta_portada.exists():
        return

    imagen_base64 = (
        "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
        "2wBDAf//////////////////////////////////////////////////////////////////////////////////////"
        "wAARCAABAAEDASIAAhEBAxEB/8QAFwAAAwEAAAAAAAAAAAAAAAAAAAECCP/EABQBAQAAAAAAAAAAAAAAAAAAAAD/"
        "2gAMAwEAAhADEAAAAf8A/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPwB//8QAFBABAAAAAAAAAAAAAAAAAAAA"
        "AP/aAAgBAgEBPwB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwB//9k="
    )
    ruta_portada.write_bytes(base64.b64decode(imagen_base64))


# Inicializar DB
init_db()
asegurar_portada_por_defecto()

#esta es la configuracion para que no de problemas de cors, basicamente le dice al navegador que si, 
#que puede hacer peticiones
origins = settings.cors_allow_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.18.193:3000",
        "https://vainillaga-frontend-re.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Montar rutas de la API
app.include_router(personal.router, prefix="/personal", tags=["Panel_Personal"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(mangas.router, prefix="/mangas", tags=["Mangas"])
app.include_router(capitulos.router, prefix="/capitulos", tags=["Capítulos"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(comentario.router, prefix="/comentarios", tags=["Comentarios"])

# Servir archivos estáticos (portadas y capítulos), si no se mandan desde nginx se pueden activar
#app.mount(settings.static_portadas_path, StaticFiles(directory=settings.resources_portadas_dir), name="portadas")
#app.mount(settings.static_capitulos_path, StaticFiles(directory=settings.resources_capitulos_dir), name="capitulos")
#app.mount(settings.static_logos_path, StaticFiles(directory=settings.resources_logos_dir), name="logos")

@app.get("/")
def home():
    return {"mensaje": "Bienvenido a VaiinllaGA"}

