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

    -- Inserción del usuario Administrador por defecto
    INSERT INTO usuarios (nombre_usuario, correo, clave_hash, rol)
    SELECT 'ZF', 'elmandangas@gmail.com', '$argon2i$v=19$m=16,t=2,p=1$Y0ltaTNibmVkR2M4UHNMcA$IHAk7elox7re7wngmV5gvw', 'admin'
    WHERE NOT EXISTS (
        SELECT 1 FROM usuarios WHERE nombre_usuario = 'ZF' OR correo = 'elmandangas@gmail.com'
    );

    -- Inserción de Géneros
    INSERT OR IGNORE INTO generos (nombre) VALUES 
    ('Acción'), ('Aventura'), ('Fantasía'), ('Terror'), ('Ciencia Ficción'), 
    ('Drama'), ('Psicológico'), ('Sobrenatural'), ('Artes Marciales'), ('Seinen');

    -- Inserción de 10 Mangas MVP
    INSERT INTO mangas (id, titulo, descripcion, tipo, url_portada, estado_publicacion, capitulos_totales, nota_general, autor, fecha_creacion, Ecchi) VALUES 
    (1, 'Dragon Ball', 'Goku y la búsqueda de las esferas del dragón.', 'manga', '/static/portadas/1.jpg', 'finalizado', 519, 9.5, 'Akira Toriyama', '1984-11-20', 0),
    (2, 'Akira', 'Ciberpunk en un Neo-Tokyo post-apocalíptico.', 'manga', '/static/portadas/2.jpg', 'finalizado', 120, 9.8, 'Katsuhiro Otomo', '1982-12-06', 0),
    (3, 'Berserk', 'La épica y oscura historia de Guts, el guerrero negro.', 'manga', '/static/portadas/3.jpg', 'emision', 373, 9.9, 'Kentaro Miura', '1989-08-25', 0),
    (4, 'Monster', 'Un cirujano busca a un monstruo que él mismo salvó.', 'manga', '/static/portadas/4.jpg', 'finalizado', 162, 9.7, 'Naoki Urasawa', '1994-12-01', 0),
    (5, 'Slam Dunk', 'Hanamichi Sakuragi y su camino en el baloncesto.', 'manga', '/static/portadas/5.jpg', 'finalizado', 276, 9.3, 'Takehiko Inoue', '1990-10-01', 0),
    (6, 'Ghost in the Shell', 'La Mayor Motoko Kusanagi explora la identidad cibernética.', 'manga', '/static/portadas/6.jpg', 'finalizado', 11, 9.0, 'Masamune Shirow', '1989-05-01', 1),
    (7, 'Saint Seiya', 'Los caballeros de bronce protegen a la diosa Atenea.', 'manga', '/static/portadas/7.jpg', 'finalizado', 110, 8.5, 'Masami Kurumada', '1986-01-01', 0),
    (8, 'Rurouni Kenshin', 'Un samurái errante jura no volver a matar.', 'manga', '/static/portadas/8.jpg', 'finalizado', 255, 9.1, 'Nobuhiro Watsuki', '1994-04-12', 0),
    (9, 'Uzumaki', 'Una ciudad obsesionada y maldecida por espirales.', 'manga', '/static/portadas/9.jpg', 'finalizado', 20, 9.5, 'Junji Ito', '1998-01-01', 0),
    (10, 'Hokuto no Ken', 'Artes marciales letales en un futuro desértico.', 'manga', '/static/portadas/10.jpg', 'finalizado', 245, 8.7, 'Buronson', '1983-09-13', 0);

    -- Relación Mangas-Géneros
    INSERT INTO mangas_generos (id_manga, id_genero) VALUES 
    (1,1), (1,2), (1,9), (2,5), (2,10), (3,1), (3,3), (3,10), (4,7), (4,10), (5,1), (5,6), 
    (6,5), (6,10), (7,1), (7,3), (8,1), (8,9), (9,4), (9,8), (10,1), (10,9);

    -- Primer Capítulo de cada Manga
    INSERT INTO capitulos (id, titulo, id_manga, numero) VALUES 
    (1, 'Bulma y Son Goku', 1, 1), (2, 'Tetsuo', 2, 1), (3, 'El Guerrero Negro', 3, 1), 
    (4, 'Dr. Tenma', 4, 1), (5, 'Sakuragi', 5, 1), (6, 'Sección 9', 6, 1), 
    (7, 'La Armadura', 7, 1), (8, 'El Vagabundo', 8, 1), (9, 'La Espiral', 9, 1), (10, 'Shin', 10, 1);

    -- Páginas para el primer capítulo de cada manga (todas apuntan a la misma imagen de ejemplo)
    INSERT INTO paginas (id_capitulo, numero, url_pagina) VALUES 
    (1, 1, '/static/capitulos/paginaEj.png'), (2, 1, '/static/capitulos/paginaEj.png'), 
    (3, 1, '/static/capitulos/paginaEj.png'), (4, 1, '/static/capitulos/paginaEj.png'),
    (5, 1, '/static/capitulos/paginaEj.png'), (6, 1, '/static/capitulos/paginaEj.png'),
    (7, 1, '/static/capitulos/paginaEj.png'), (8, 1, '/static/capitulos/paginaEj.png'),
    (9, 1, '/static/capitulos/paginaEj.png'), (10, 1, '/static/capitulos/paginaEj.png');

    -- Comentarios (Usando el ID 1 del usuario ZF)
    INSERT INTO comentarios (id_usuario, id_manga, texto, likes) VALUES 
    (1, 1, 'El inicio de una leyenda.', 50), (1, 2, 'Obra maestra del ciberpunk.', 40),
    (1, 3, 'Simplemente arte.', 100), (1, 4, 'Suspenso de primer nivel.', 30),
    (1, 5, 'El mejor manga de deportes.', 20), (1, 6, 'Muy profundo filosóficamente.', 15),
    (1, 7, 'Nostalgia pura de los 80.', 25), (1, 8, 'Excelente evolución de personaje.', 18),
    (1, 9, 'Inquietante como todo lo de Ito.', 60), (1, 10, 'Ya estás muerto.', 45);
    """)
    conn.commit()
    conn.close()