from app.db.conector import get_connection
import asyncio


async def sacar_nota_media() -> str:
    def _calcular() -> str:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.titulo, AVG(um.puntuacion) AS nota_media, COUNT(um.puntuacion) AS votos
                FROM mangas m
                LEFT JOIN usuarios_mangas um ON m.id = um.id_manga
                GROUP BY m.id, m.titulo;
                """
            )

            result = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, col in enumerate(cursor.description):
                    row_dict[col[0]] = row[i]
                result.append(row_dict)

            for row in result:
                manga_id = row["id"]
                nota_media = row["nota_media"]

                cursor.execute(
                    """
                    UPDATE mangas
                    SET nota_general = ?
                    WHERE id = ?;
                    """,
                    (nota_media, manga_id),
                )

            conn.commit()
            return "ha salido bien"
        finally:
            cursor.close()
            conn.close()

    return await asyncio.to_thread(_calcular)
