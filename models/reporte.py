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

    def tiempo_promedio_general(self):
        """
        Tiempo promedio de respuesta (horas) en general, para el panel resumen (req. #10).
        Desde que se registra la incidencia hasta su primer 'Resuelto'/'Cerrado'.
        Devuelve 0 si aun no hay casos resueltos.
        """
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute("""
            SELECT ROUND(AVG(TIMESTAMPDIFF(HOUR, i.fecha, h.fecha)), 1) AS horas
            FROM incidencia i
            INNER JOIN (
                SELECT id_incidencia, MIN(fecha) AS fecha
                FROM estado_incidencia
                WHERE id_estado IN (5, 6)
                GROUP BY id_incidencia
            ) h ON h.id_incidencia = i.id
        """)
        fila = cursor.fetchone()
        cursor.close()
        con.close()
        return (fila['horas'] if fila and fila['horas'] is not None else 0)

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

    def por_categoria_rango(self, fecha_desde=None, fecha_hasta=None):
        """
        Incidencias por tipo (categoria) dentro de un rango de fechas (req. web #9).
        Si no se pasan fechas, cuenta todas.
        """
        con = Conexion().open
        cursor = con.cursor()
        sql = """
            SELECT c.nombre AS etiqueta, COUNT(i.id) AS cantidad
            FROM categoria c
            LEFT JOIN incidencia i ON i.id_categoria = c.id
        """
        params = []
        condiciones = []
        if fecha_desde:
            condiciones.append("i.fecha >= %s")
            params.append(fecha_desde + ' 00:00:00')
        if fecha_hasta:
            condiciones.append("i.fecha <= %s")
            params.append(fecha_hasta + ' 23:59:59')
        if condiciones:
            # El filtro va dentro del LEFT JOIN para no perder categorias con 0.
            sql += " AND " + " AND ".join(condiciones)
        sql += " GROUP BY c.id, c.nombre ORDER BY cantidad DESC"
        cursor.execute(sql, params)
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def tiempo_promedio_por_tipo(self):
        """
        Tiempo promedio de atencion por tipo de caso, en horas (req. web #9).
        Se mide desde que se registra la incidencia hasta que pasa a
        'Resuelto' (5) o 'Cerrado' (6) por primera vez.
        """
        sql = """
            SELECT
                c.nombre AS etiqueta,
                ROUND(AVG(TIMESTAMPDIFF(HOUR, i.fecha, h.fecha)), 1) AS horas
            FROM incidencia i
            INNER JOIN categoria c ON i.id_categoria = c.id
            INNER JOIN (
                SELECT id_incidencia, MIN(fecha) AS fecha
                FROM estado_incidencia
                WHERE id_estado IN (5, 6)
                GROUP BY id_incidencia
            ) h ON h.id_incidencia = i.id
            GROUP BY c.id, c.nombre
            ORDER BY horas DESC
        """
        return self._agrupado(sql)

    def resueltas_con_calificacion(self):
        """
        Incidencias resueltas/cerradas con su calificacion y comentario (req. web #9).
        """
        sql = """
            SELECT
                i.id,
                i.descripcion,
                e.nombre AS estado,
                cal.puntuacion,
                cal.comentario
            FROM calificacion cal
            INNER JOIN incidencia i ON cal.id_incidencia = i.id
            INNER JOIN estado e ON i.id_estado = e.id
            ORDER BY i.id
        """
        return self._agrupado(sql)

    def incidencias_geo(self):
        """Incidencias con coordenadas para el reporte geografico (req. web #8)."""
        sql = """
            SELECT
                i.id,
                i.descripcion,
                i.latitud,
                i.longitud,
                e.nombre AS estado,
                COALESCE(c.nombre, 'Sin categoria') AS categoria,
                COALESCE(ur.nombre, '-') AS urgencia
            FROM incidencia i
            INNER JOIN estado e ON i.id_estado = e.id
            LEFT JOIN categoria c ON i.id_categoria = c.id
            LEFT JOIN urgencia ur ON i.id_urgencia = ur.id
            WHERE i.latitud IS NOT NULL AND i.longitud IS NOT NULL
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
