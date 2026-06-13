# ============================================================
#  models/evidencia.py  -  Evidencias (fotos) de una incidencia
# ------------------------------------------------------------
#  Permite adjuntar varias imagenes a una incidencia (req. #4 y #14).
#  Aqui solo se guarda/lee el NOMBRE del archivo; el archivo fisico
#  lo maneja la ruta (routes/api.py) en la carpeta de uploads.
# ============================================================
from conexionBD import Conexion


class Evidencia:

    def registrar(self, id_incidencia, nombre_archivo):
        """Guarda el nombre de archivo de una evidencia y devuelve su id."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO evidencia (id_incidencia, url_imagen) VALUES (%s, %s)",
            [id_incidencia, nombre_archivo]
        )
        nuevo_id = cursor.lastrowid
        con.commit()
        cursor.close()
        con.close()
        return nuevo_id

    def listar(self, id_incidencia):
        """Lista las evidencias (id, id_incidencia, url_imagen) de una incidencia."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, id_incidencia, url_imagen FROM evidencia WHERE id_incidencia = %s ORDER BY id",
            [id_incidencia]
        )
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado
