from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TipoManga(str, Enum):
    manga = "manga"
    manhwa = "manhwa"
    manhua = "manhua"
    oneShot = "OneShot"


class EstadoManga(str, Enum):
    en_emision="emision"
    finalizado="finalizado"
    en_pausa="pausa"


class MangaBase(BaseModel):
    titulo: str
    descripcion: str
    tipo: TipoManga  
    estado_publicacion: EstadoManga
    generos: list[str]
    autor: str
    echi: bool


class MangaRespuesta(MangaBase):
    id: int
    url_portada: Optional[str]
    nota_general: Optional[float]


class MangaUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    tipo: TipoManga | None = None
    estado_publicacion: EstadoManga | None = None
    capitulos_totales: int | None = None
    nota_general: float | None = None
    autor: str | None = None
    generos: list[str] | None = None

class MangaUpdatePersonal(BaseModel):
    estado_lectura: str | None = None
    puntuacion: float | None = None
    comentario_personal: str | None = None
    id_ultimo_capitulo_leido: int | None = None



class MangaQuery(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    estado_publicacion: Optional[str] = None
    generos: Optional[str] = None
    autor: Optional[str] = None
    capitulos_totales: Optional[int] = None