# ============================================================
#  models/notificacion.py  -  Notificaciones del usuario (req. #9)
# ------------------------------------------------------------
#  Guarda el historial de notificaciones que recibe un usuario
#  (caso recibido, cambio de estado, derivado, cerrado, etc.).
#  El envio push real lo hace tools/fcm.py; aqui solo la BD.
# ============================================================
from conexionBD import Conexion


class Notificacion:

    def listar(self, id_usuario):
        """Lista las notificaciones de un usuario, de la mas reciente a la mas antigua."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            """SELECT id, id_usuario, mensaje, fecha, estado
               FROM notificacion
               WHERE id_usuario = %s
               ORDER BY fecha DESC, id DESC""",
            [id_usuario]
        )
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def crear(self, id_usuario, mensaje):
        """Crea una notificacion (estado 0 = no leida) y devuelve su id."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO notificacion (id_usuario, mensaje) VALUES (%s, %s)",
            [id_usuario, mensaje]
        )
        nuevo_id = cursor.lastrowid
        con.commit()
        cursor.close()
        con.close()
        return nuevo_id

    def marcar_leida(self, id_notificacion):
        """Marca una notificacion como leida (estado = 1)."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute("UPDATE notificacion SET estado = 1 WHERE id = %s", [id_notificacion])
        con.commit()
        cursor.close()
        con.close()
        return True
