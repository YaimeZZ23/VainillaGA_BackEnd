from fastapi import APIRouter, Depends, HTTPException
from app.db.conector import get_connection
from app.models.usuario import UsuarioRespuesta, UsuarioUpdate, UsuarioBusqueda
from fastapi.security import OAuth2PasswordBearer
from app.utils.seguridad import decodificar_y_validar_token
from typing import Optional
import asyncio


##! EL tokenUrl="/auth/login", SOLO SIRVE PARA LA DOCUMENTACION
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=None)

router = APIRouter()

##TODO AQUI EL TOQUEN LO VA A PROPORCIONAR LA CLASE ESPECIAL DE FAST API, OAuth2PasswordBearer
##TODO ESTA COGE EL APARATADO DE LA CONTRASENA BEARER DEL HEADER EN CADA HTTP

##TODO ESTA FUNCION EN CONCRETO MANDA VERIFICAR EL TOKEN Y DEVUELVE LA INFOMACION QUE TIENE DENTRO,
##TODO EN ESTE CASO LA INFORMACION DEL USUARIO QUE HEMOS METIDO NOSOTROS EN SU CREACION
def get_usuario_actual(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="No autentificado")
    try:
        payload = decodificar_y_validar_token(token)
        return payload  # aquí se podria devolver más info o usuario completo o lo que quieras
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    


##todo ESTA FUNCION ES COMO LA DE ARRIBA PERO HACIENDO QUE NO SALTA CODIGO DE ERROR ES PARA UNA VALIDACION OPCIONAL
def get_usuario_actual_opcional(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        return None
    try:
        payload = decodificar_y_validar_token(token)
        return payload
    except Exception:
        return None

##todo CUANDO SE LLEMA A UNA FUNCION CON DEPENDES, EL PARAMETRO, EN ESTE CASO EL current_user, 
#TODO SE LA VA A PROPORCIONAR LA FUNCION DENTRO DEL DEPENDS
@router.get("/me", response_model=UsuarioRespuesta)
async def obtener_informacion_usuario(current_user: dict = Depends(get_usuario_actual)):
    def _obtener():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (current_user["id"],))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return dict(usuario)
        finally:
            conn.close()

    return await asyncio.to_thread(_obtener)


@router.delete("/{user_id}")
async def borrar_usuario(user_id: int, usuario_actual: dict = Depends(get_usuario_actual)):
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=401, detail="No estas autorizado para esta accion")

    def _borrar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            conn.commit()
            return {"usuario borrado": usuario}
        finally:
            conn.close()

    return await asyncio.to_thread(_borrar)


@router.put("/{user_id}", response_model=UsuarioRespuesta)
async def actualizar_usuario(user_id: int, datos: UsuarioUpdate, usuario_actual: dict = Depends(get_usuario_actual)):
    def _actualizar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            fila = cursor.fetchone()
            if not fila:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            if usuario_actual["rol"] != "admin" and usuario_actual["id"] != user_id:
                raise HTTPException(status_code=401, detail="No estás autorizado para modificar este usuario")

            campos = []
            datos_dados = []

            if datos.nombre_usuario:
                campos.append("nombre_usuario = ?")
                datos_dados.append(datos.nombre_usuario)
            if datos.correo:
                campos.append("correo = ?")
                datos_dados.append(datos.correo)
            if datos.clave_hash:
                campos.append("clave_hash = ?")
                datos_dados.append(datos.clave_hash)
            if datos.rol and usuario_actual["rol"] == "admin":
                campos.append("rol = ?")
                datos_dados.append(datos.rol)

            if not campos:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

            set_clause = ", ".join(campos)
            query = f"UPDATE usuarios SET {set_clause} WHERE id = ?"
            datos_dados.append(user_id)

            cursor.execute(query, datos_dados)
            conn.commit()

            cursor.execute("SELECT id, nombre_usuario, correo, rol FROM usuarios WHERE id = ?", (user_id,))
            fila = cursor.fetchone()
            return dict(fila)
        finally:
            conn.close()

    return await asyncio.to_thread(_actualizar)

@router.get("/")
async def listar_usuarios(
    rol: Optional[str] = None,
    nombre_usuario: Optional[str] = None,
    cliente = Depends(get_usuario_actual)
):
    if cliente["rol"] != "admin":
        raise HTTPException(status_code=401, detail="No estás autorizado para ver todos los usuarios")

    def _listar():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT id, nombre_usuario, correo, rol, fecha_creacion FROM usuarios"
            condiciones = []
            valores = []

            if rol:
                condiciones.append("rol = ?")
                valores.append(rol)
            if nombre_usuario:
                condiciones.append("nombre_usuario = ?")
                valores.append(nombre_usuario)

            if condiciones:
                query += " WHERE " + " AND ".join(condiciones)

            query += " ORDER BY fecha_creacion DESC"

            cursor.execute(query, valores)
            filas = cursor.fetchall()
            return filas
        finally:
            conn.close()

    return await asyncio.to_thread(_listar)

