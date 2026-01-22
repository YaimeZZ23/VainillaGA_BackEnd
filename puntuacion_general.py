import sqlite3
from app.db.conector import get_connection

def sacar_nota_media():


    conn = get_connection()
    cursor = conn.cursor()
    # Calcular nota media y número de votos por manga
    cursor.execute("""
        SELECT m.id, m.titulo, AVG(um.puntuacion) AS nota_media, COUNT(um.puntuacion) AS votos
        FROM mangas m
        LEFT JOIN usuarios_mangas um ON m.id = um.id_manga
        GROUP BY m.id, m.titulo;
    """)

    rows = cursor.fetchall()
    cols = [c[0] for c in cursor.description]
    result = [dict(zip(cols, row)) for row in rows]
    print(result)
    # Actualizar nota_general en la tabla mangas
    for row in result:
        manga_id = row["id"]
        nota_media = row["nota_media"]

        cursor.execute("""
            UPDATE mangas
            SET nota_general = ?
            WHERE id = ?;
        """, (nota_media, manga_id))

    conn.commit()
    cursor.close()
    conn.close()

    # Devolver en formato JSON
    #return json.dumps(result, indent=2)
    return "ha salido bien"




print(sacar_nota_media())

