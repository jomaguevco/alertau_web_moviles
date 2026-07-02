# ============================================================
#  models/mensaje.py  -  Chat asociado a una incidencia
# ------------------------------------------------------------
#  Permite al personal responder/seguir el caso por chat
#  (req. web #7 y req. movil #10).
# ============================================================
from conexionBD import Conexion


class Mensaje:

    def listar(self, incidencia_id):
        """Lista los mensajes del chat de una incidencia, en orden cronologico."""
        con = Conexion().open
        cursor = con.cursor()
        sql = """
            SELECT
                m.id,
                m.mensaje,
                m.fecha,
                m.id_usuario,
                CONCAT(u.nombres, ' ', u.apellidos) AS autor,
                t.nombre AS rol_autor
            FROM mensaje m
            INNER JOIN usuario u      ON m.id_usuario = u.id
            INNER JOIN tipo_usuario t ON u.id_tipo_usuario = t.id
            WHERE m.id_incidencia = %s
            ORDER BY m.fecha ASC, m.id ASC
        """
        cursor.execute(sql, [incidencia_id])
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def listar_movil(self, incidencia_id):
        """Lista los mensajes con los campos que espera el modelo Mensaje de la app,
        incluyendo autor y rol para que el chat movil muestre quien envia cada mensaje."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            """SELECT m.id, m.id_incidencia, m.id_usuario, m.mensaje, m.fecha,
                      CONCAT(u.nombres, ' ', u.apellidos) AS autor,
                      t.nombre AS rol_autor
               FROM mensaje m
               INNER JOIN usuario u      ON m.id_usuario = u.id
               INNER JOIN tipo_usuario t ON u.id_tipo_usuario = t.id
               WHERE m.id_incidencia = %s ORDER BY m.fecha ASC, m.id ASC""",
            [incidencia_id]
        )
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def enviar(self, incidencia_id, id_usuario, texto):
        """Guarda un nuevo mensaje de texto en el chat de la incidencia."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO mensaje (id_incidencia, id_usuario, mensaje) VALUES (%s, %s, %s)",
            [incidencia_id, id_usuario, texto]
        )
        con.commit()
        cursor.close()
        con.close()
        return True
