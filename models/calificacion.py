# ============================================================
#  models/calificacion.py  -  Calificacion de la atencion (req. #11)
# ------------------------------------------------------------
#  Una calificacion por incidencia (1..5) + comentario. Solo se
#  permite calificar una vez (la BD tiene un UNIQUE por incidencia).
# ============================================================
from conexionBD import Conexion


class Calificacion:

    def obtener(self, id_incidencia):
        """Devuelve la calificacion de una incidencia, o None si aun no tiene."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, id_incidencia, puntuacion, comentario FROM calificacion WHERE id_incidencia = %s",
            [id_incidencia]
        )
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        return resultado

    def registrar(self, id_incidencia, puntuacion, comentario):
        """
        Registra la calificacion de una incidencia.
        Devuelve (True, id) o (False, mensaje) si ya existia o hubo error.
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            # Evitar doble calificacion (ademas del UNIQUE de la BD).
            cursor.execute("SELECT id FROM calificacion WHERE id_incidencia = %s", [id_incidencia])
            if cursor.fetchone():
                return False, "Esta incidencia ya fue calificada"

            cursor.execute(
                "INSERT INTO calificacion (id_incidencia, puntuacion, comentario) VALUES (%s, %s, %s)",
                [id_incidencia, puntuacion, comentario]
            )
            nuevo_id = cursor.lastrowid
            con.commit()
            return True, nuevo_id
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            cursor.close()
            con.close()
