from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
TIEMPO_EXPIRACION = settings.jwt_exp_minutes

# OBJETO ENCRIPTADOR usando Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def contraseña_hash(password: str) -> str:
    return pwd_context.hash(password)

def veificar_contraseña(contraseña_sin_hashear, contraseña_hasheada) -> bool:
    return pwd_context.verify(contraseña_sin_hashear, contraseña_hasheada)

def crear_token(datos: dict):
    a_codificar = datos.copy()
    expira = datetime.utcnow() + timedelta(minutes=TIEMPO_EXPIRACION)
    a_codificar.update({"exp": expira})
    return jwt.encode(a_codificar, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_y_validar_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
