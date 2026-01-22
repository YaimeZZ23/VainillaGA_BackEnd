from fastapi import APIRouter, HTTPException
import asyncio
from app.db.conector import get_connection
from app.models.usuario import UsuarioRegistro, UsuarioLogin
from app.utils.seguridad import contraseña_hash, veificar_contraseña, crear_token

router = APIRouter()


##todo Se crea el usuario en base de datos
@router.post("/registro")
async def registro(user: UsuarioRegistro):
    def _registro():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre_usuario, correo, clave_hash, rol) VALUES (?, ?, ?, ?)",
                (user.nombre_usuario, user.correo, contraseña_hash(user.clave), "basico"),
            )
            conn.commit()
            return {"msg": "Usuario registrado correctamente"}
        except Exception:
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        finally:
            conn.close()

    return await asyncio.to_thread(_registro)

@router.post("/login")
async def login(user: UsuarioLogin):
    def _login():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, clave_hash, rol FROM usuarios WHERE nombre_usuario = ?",
            (user.nombre_usuario,),
        )
        row = cursor.fetchone()
        if not row or not veificar_contraseña(user.clave, row["clave_hash"]):
            conn.close()
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        token = crear_token({"id": row["id"], "nombre_usuario": user.nombre_usuario, "rol": row["rol"]})
        conn.close()
        return {"access_token": token, "token_type": "bearer"}

    return await asyncio.to_thread(_login)
