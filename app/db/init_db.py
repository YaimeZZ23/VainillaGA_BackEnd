from app.db.conector import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    -- [ESQUEMA DE TABLAS]
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

    -- [INSERCIÓN DE DATOS]

    -- 1. Usuarios (ZF=1, prueba=2)
    INSERT INTO usuarios (id, nombre_usuario, correo, clave_hash, rol) VALUES 
    (1, 'ZF', 'elmandangas@gmail.com', '$argon2i$v=19$m=16,t=2,p=1$Y0ltaTNibmVkR2M4UHNMcA$IHAk7elox7re7wngmV5gvw', 'basico'),
    (2, 'prueba', 'usuario@gmail.com', '$argon2i$v=19$m=16,t=2,p=1$Y0ltaTNibmVkR2M4UHNMcA$IHAk7elox7re7wngmV5gvw', 'basico')
    ON CONFLICT DO NOTHING;

    -- 2. Géneros
    INSERT OR IGNORE INTO generos (nombre) VALUES 
    ('Acción'), ('Aventura'), ('Fantasía'), ('Terror'), ('Ciencia Ficción'), 
    ('Drama'), ('Psicológico'), ('Sobrenatural'), ('Artes Marciales'), ('Seinen'), ('Deportes');

    -- 3. Mangas (15 Clásicos)
    INSERT INTO mangas (id, titulo, descripcion, tipo, url_portada, estado_publicacion, capitulos_totales, nota_general, autor, fecha_creacion, Ecchi) VALUES 
    (1, 'Dragon Ball', 'Goku y la búsqueda de las esferas.', 'manga', '/static/portadas/1.jpg', 'finalizado', 519, 9.5, 'Akira Toriyama', '1984-11-20', 0),
    (2, 'Akira', 'Ciberpunk en Neo-Tokyo.', 'manga', '/static/portadas/2.jpg', 'finalizado', 120, 9.8, 'Katsuhiro Otomo', '1982-12-06', 0),
    (3, 'Berserk', 'La historia de Guts.', 'manga', '/static/portadas/3.jpg', 'emision', 373, 9.9, 'Kentaro Miura', '1989-08-25', 0),
    (4, 'Monster', 'Cirujano vs Monstruo.', 'manga', '/static/portadas/4.jpg', 'finalizado', 162, 9.7, 'Naoki Urasawa', '1994-12-01', 0),
    (5, 'Slam Dunk', 'Baloncesto y pasión.', 'manga', '/static/portadas/5.jpg', 'finalizado', 276, 9.3, 'Takehiko Inoue', '1990-10-01', 0),
    (6, 'Ghost in the Shell', 'Identidad cibernética.', 'manga', '/static/portadas/6.jpg', 'finalizado', 11, 9.0, 'Masamune Shirow', '1989-05-01', 1),
    (7, 'Saint Seiya', 'Caballeros de Atenea.', 'manga', '/static/portadas/7.jpg', 'finalizado', 110, 8.5, 'Masami Kurumada', '1986-01-01', 0),
    (8, 'Rurouni Kenshin', 'El samurái errante.', 'manga', '/static/portadas/8.jpg', 'finalizado', 255, 9.1, 'Nobuhiro Watsuki', '1994-04-12', 0),
    (9, 'Uzumaki', 'Maldición de espirales.', 'manga', '/static/portadas/9.jpg', 'finalizado', 20, 9.5, 'Junji Ito', '1998-01-01', 0),
    (10, 'Hokuto no Ken', 'Artes marciales post-apocalípticas.', 'manga', '/static/portadas/10.jpg', 'finalizado', 245, 8.7, 'Buronson', '1983-09-13', 0),
    (11, 'Vagabond', 'La vida de Musashi Miyamoto.', 'manga', '/static/portadas/11.jpg', 'pausa', 327, 9.9, 'Takehiko Inoue', '1998-09-01', 0),
    (12, 'JoJo Bizarre Adventure', 'Linaje Joestar.', 'manga', '/static/portadas/12.jpg', 'emision', 900, 9.2, 'Hirohiko Araki', '1987-01-01', 0),
    (13, 'Yu Yu Hakusho', 'Detective espiritual.', 'manga', '/static/portadas/13.jpg', 'finalizado', 175, 9.0, 'Yoshihiro Togashi', '1990-12-03', 0),
    (14, 'Detective Conan', 'Niño detective.', 'manga', '/static/portadas/14.jpg', 'emision', 1100, 9.0, 'Gosho Aoyama', '1994-01-19', 0),
    (15, 'Ashita no Joe', 'Boxeo y drama social.', 'manga', '/static/portadas/15.jpg', 'finalizado', 171, 9.6, 'Asao Takamori', '1968-01-01', 0)
    ON CONFLICT(id) DO NOTHING;

    -- 4. Capítulos (1 por manga)
    INSERT INTO capitulos (id, titulo, id_manga, numero) VALUES 
    (1,'Capítulo 1',1,1), (2,'Capítulo 1',2,1), (3,'Capítulo 1',3,1), (4,'Capítulo 1',4,1), (5,'Capítulo 1',5,1),
    (6,'Capítulo 1',6,1), (7,'Capítulo 1',7,1), (8,'Capítulo 1',8,1), (9,'Capítulo 1',9,1), (10,'Capítulo 1',10,1),
    (11,'Capítulo 1',11,1), (12,'Capítulo 1',12,1), (13,'Capítulo 1',13,1), (14,'Capítulo 1',14,1), (15,'Capítulo 1',15,1)
    ON CONFLICT(id) DO NOTHING;

    -- 5. Páginas (2 por capítulo: paginaEj y paginaEj2)
    INSERT INTO paginas (id_capitulo, numero, url_pagina) VALUES 
    (1,1,'/static/capitulos/paginaEj.png'), (1,2,'/static/capitulos/paginaEj2.png'),
    (2,1,'/static/capitulos/paginaEj.png'), (2,2,'/static/capitulos/paginaEj2.png'),
    (3,1,'/static/capitulos/paginaEj.png'), (3,2,'/static/capitulos/paginaEj2.png'),
    (4,1,'/static/capitulos/paginaEj.png'), (4,2,'/static/capitulos/paginaEj2.png'),
    (5,1,'/static/capitulos/paginaEj.png'), (5,2,'/static/capitulos/paginaEj2.png'),
    (6,1,'/static/capitulos/paginaEj.png'), (6,2,'/static/capitulos/paginaEj2.png'),
    (7,1,'/static/capitulos/paginaEj.png'), (7,2,'/static/capitulos/paginaEj2.png'),
    (8,1,'/static/capitulos/paginaEj.png'), (8,2,'/static/capitulos/paginaEj2.png'),
    (9,1,'/static/capitulos/paginaEj.png'), (9,2,'/static/capitulos/paginaEj2.png'),
    (10,1,'/static/capitulos/paginaEj.png'), (10,2,'/static/capitulos/paginaEj2.png'),
    (11,1,'/static/capitulos/paginaEj.png'), (11,2,'/static/capitulos/paginaEj2.png'),
    (12,1,'/static/capitulos/paginaEj.png'), (12,2,'/static/capitulos/paginaEj2.png'),
    (13,1,'/static/capitulos/paginaEj.png'), (13,2,'/static/capitulos/paginaEj2.png'),
    (14,1,'/static/capitulos/paginaEj.png'), (14,2,'/static/capitulos/paginaEj2.png'),
    (15,1,'/static/capitulos/paginaEj.png'), (15,2,'/static/capitulos/paginaEj2.png')
    ON CONFLICT DO NOTHING;

    -- 6. Comentarios y Biblioteca del usuario 'prueba'
    INSERT INTO comentarios (id_usuario, id_manga, texto, likes) VALUES 
    (1, 3, 'El mejor seinen.', 100);

    INSERT INTO usuarios_mangas (id_usuario, id_manga, estado_lectura, puntuacion, comentario_personal, id_ultimo_capitulo_leido) VALUES 
    (2, 3, 'leyendo', 10.0, 'Impactante.', 3),
    (2, 1, 'completado', 9.0, 'Imprescindible.', 1),
    (2, 15, 'favorito', 9.8, 'Una joya oculta.', 15),
    (2, 14, 'favorito', 9.5, 'Mejor que Auguste Dupin.', 14),
    (2, 12, 'pendiente', null, 'Posible obra maestra.', 12);
    """)
    conn.commit()
    conn.close()