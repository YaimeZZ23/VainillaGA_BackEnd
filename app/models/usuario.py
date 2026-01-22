from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class TipoRol(str, Enum):
    basico = "basico"
    scan = "scan"
    admin = "admin"

class UsuarioRegistro(BaseModel):
    nombre_usuario: str
    correo: str
    clave: str

class UsuarioLogin(BaseModel):
    nombre_usuario: str
    clave: str

class UsuarioRespuesta(BaseModel):
    id: int
    nombre_usuario: str
    correo: str
    rol: str

class UsuarioUpdate(BaseModel):
    nombre_usuario: str | None = None
    correo: str | None = None
    rol: str | None = None 
    clave_hash: str | None = None

class UsuarioBusqueda(BaseModel):
    nombre_usuario: str | None = None
    rol: str | None = None 


