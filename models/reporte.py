# ============================================================
#  models/reporte.py  -  Indicadores para el PANEL RESUMEN
# ------------------------------------------------------------
#  Calcula los numeros que se muestran en el dashboard
#  (req. web #10) y los reportes administrativos (req. web #9):
#   - resumen()       : tarjetas con indicadores clave
#   - por_categoria() : incidencias por tipo
#   - por_urgencia()  : incidencias por nivel de urgencia
#   - por_estado()    : incidencias por estado
# ============================================================
from conexionBD import Conexion


class Reporte:

    def resumen(self):
        """
        Devuelve un diccionario con los indicadores clave del panel:
        total de incidencias, casos criticos, cerradas, abiertas y % de cierre.
        """
        con = Conexion().open
        cursor = con.cursor()

        # Una sola consulta calcula varios contadores usando SUM(CASE...).
        # id_estado 6 = 'Cerrado'. id_urgencia 4 = 'Critica'.
        sql = """
            SELECT
                COUNT(*)                                              AS total,
                SUM(CASE WHEN i.id_urgencia = 4 OR i.es_alerta_rapida = 1
                         THEN 1 ELSE 0 END)                           AS criticas,
                SUM(CASE WHEN i.id_estado = 6 THEN 1 ELSE 0 END)      AS cerradas,
                SUM(CASE WHEN i.id_estado <> 6 THEN 1 ELSE 0 END)     AS abiertas
            FROM incidencia i
        """
        cursor.execute(sql)
        fila = cursor.fetchone()

        cursor.close()
        con.close()

        total = fila['total'] or 0
        cerradas = fila['cerradas'] or 0
        # Porcentaje de casos cerrados (evitando division por cero).
        pct_cerradas = round((cerradas / total) * 100, 1) if total else 0.0

        return {
            'total': total,
            'criticas': fila['criticas'] or 0,
            'cerradas': cerradas,
            'abiertas': fila['abiertas'] or 0,
            'pct_cerradas': pct_cerradas,
        }

    def por_categoria(self):
        """Cantidad de incidencias agrupadas por categoria (tipo)."""
        sql = """
            SELECT c.nombre AS etiqueta, COUNT(i.id) AS cantidad
            FROM categoria c
            LEFT JOIN incidencia i ON i.id_categoria = c.id
            GROUP BY c.id, c.nombre
            ORDER BY cantidad DESC
        """
        return self._agrupado(sql)

    def por_urgencia(self):
        """Cantidad de incidencias agrupadas por nivel de urgencia."""
        sql = """
            SELECT ur.nombre AS etiqueta, COUNT(i.id) AS cantidad
            FROM urgencia ur
            LEFT JOIN incidencia i ON i.id_urgencia = ur.id
            GROUP BY ur.id, ur.nombre
            ORDER BY ur.id
        """
        return self._agrupado(sql)

    def por_estado(self):
        """Cantidad de incidencias agrupadas por estado del flujo."""
        sql = """
            SELECT e.nombre AS etiqueta, COUNT(i.id) AS cantidad
            FROM estado e
            LEFT JOIN incidencia i ON i.id_estado = e.id
            GROUP BY e.id, e.nombre
            ORDER BY e.id
        """
        return self._agrupado(sql)

    def _agrupado(self, sql):
        """Metodo interno reutilizable para las consultas de agrupacion."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado
