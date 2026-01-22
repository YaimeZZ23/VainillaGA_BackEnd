from app.db.conector import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE NOT NULL,
        correo TEXT NOT NULL,
        clave_hash TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('basico', 'scan', 'admin')) NOT NULL,                 
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS mangas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    tipo TEXT CHECK(tipo IN ('manga', 'manhwa', 'manhua', 'OneShot')) NOT NULL,
    url_portada TEXT,
    estado_publicacion TEXT CHECK(estado_publicacion IN ('emision', 'finalizado', 'pausa')) NOT NULL,
    capitulos_totales INTEGER DEFAULT 0,
    nota_general DECIMAL(3,2),
    autor TEXT,
    fecha_creacion DATE,
    fecha_actualizacion DATE DEFAULT CURRENT_DATE,
    Ecchi BOOL
    );

    CREATE TABLE IF NOT EXISTS generos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS mangas_generos (
        id_manga INTEGER NOT NULL,
        id_genero INTEGER NOT NULL,
        PRIMARY KEY (id_manga, id_genero),
        FOREIGN KEY (id_manga) REFERENCES mangas(id) ON DELETE CASCADE,
        FOREIGN KEY (id_genero) REFERENCES generos(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS capitulos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        id_manga INTEGER NOT NULL,
        numero INTEGER NOT NULL,
        FOREIGN KEY (id_manga) REFERENCES mangas(id)
    );

    CREATE TABLE IF NOT EXISTS paginas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_capitulo INTEGER NOT NULL,
        numero INTEGER NOT NULL,
        url_pagina TEXT NOT NULL,
        FOREIGN KEY (id_capitulo) REFERENCES capitulos(id)
    );

    CREATE TABLE IF NOT EXISTS usuarios_mangas (
        id_usuario INTEGER NOT NULL,
        id_manga INTEGER NOT NULL,
        estado_lectura TEXT CHECK(estado_lectura IN ('leyendo', 'completado', 'pendiente', 'abandonado', 'favorito')) NOT NULL,
        puntuacion DECIMAL(3,1) CHECK(puntuacion BETWEEN 1 AND 10),
        comentario_personal TEXT,
        id_ultimo_capitulo_leido INTEGER,
        fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id_usuario, id_manga),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (id_manga) REFERENCES mangas(id) ON DELETE CASCADE,
        FOREIGN KEY (id_ultimo_capitulo_leido) REFERENCES capitulos(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_manga INTEGER NOT NULL,
        id_comentario_padre INTEGER,
        texto TEXT NOT NULL,
        likes INTEGER,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (id_manga) REFERENCES mangas(id) ON DELETE CASCADE,
        FOREIGN KEY (id_comentario_padre) REFERENCES comentarios(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS comentarios_likes (
        id_usuario INTEGER NOT NULL,
        id_comentario INTEGER NOT NULL,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id_usuario, id_comentario),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (id_comentario) REFERENCES comentarios(id) ON DELETE CASCADE
    );
    INSERT INTO usuarios (nombre_usuario, correo, clave_hash, rol)
    SELECT 'ZF', 'elmandangas@gmail.com', '$argon2i$v=19$m=16,t=2,p=1$Y0ltaTNibmVkR2M4UHNMcA$IHAk7elox7re7wngmV5gvw', 'admin'
    WHERE NOT EXISTS (
    SELECT 1 FROM usuarios WHERE nombre_usuario = 'ZF' OR correo = 'elmandangas@gmail.com'
    );
    """)
    conn.commit()
    conn.close()
