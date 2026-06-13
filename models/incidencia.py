# ============================================================
#  models/incidencia.py  -  Acceso a datos de INCIDENCIAS
# ------------------------------------------------------------
#  Es el corazon del panel. Aqui estan las consultas para:
#   - listar()          : lista con filtros (req. web #2)
#   - obtener()         : detalle completo de una incidencia (req. web #5)
#   - listar_evidencias(): imagenes adjuntas (req. web #5)
#   - linea_tiempo()    : historial / trazabilidad (req. web #4)
#   - derivaciones()    : areas a las que fue derivada (req. web #3)
#   - cambiar_estado()  : actualizar estado con trazabilidad (req. web #4)
#   - derivar()         : derivar a un area responsable (req. web #3)
# ============================================================
from conexionBD import Conexion


class Incidencia:

    def listar(self, filtros=None):
        """
        Lista las incidencias aplicando filtros opcionales.
        'filtros' es un diccionario que puede traer: id_estado, id_categoria,
        id_urgencia, id_area, fecha_desde, fecha_hasta. Si un filtro no viene
        (o viene vacio), simplemente no se aplica.
        """
        filtros = filtros or {}

        con = Conexion().open
        cursor = con.cursor()

        # Consulta base con los JOIN para mostrar nombres en lugar de ids.
        sql = """
            SELECT
                i.id,
                i.descripcion,
                c.nombre  AS categoria,
                ur.nombre AS urgencia,
                e.nombre  AS estado,
                i.id_estado,
                CONCAT(u.nombres, ' ', u.apellidos) AS reportante,
                i.es_alerta_rapida,
                i.fecha
            FROM incidencia i
            LEFT JOIN categoria c ON i.id_categoria = c.id
            LEFT JOIN urgencia ur ON i.id_urgencia = ur.id
            INNER JOIN estado e   ON i.id_estado = e.id
            INNER JOIN usuario u  ON i.id_usuario = u.id
            WHERE 1 = 1
        """

        # Vamos agregando condiciones y parametros segun los filtros recibidos.
        params = []
        if filtros.get('id_estado'):
            sql += " AND i.id_estado = %s"
            params.append(filtros['id_estado'])
        if filtros.get('id_categoria'):
            sql += " AND i.id_categoria = %s"
            params.append(filtros['id_categoria'])
        if filtros.get('id_urgencia'):
            sql += " AND i.id_urgencia = %s"
            params.append(filtros['id_urgencia'])
        if filtros.get('fecha_desde'):
            sql += " AND i.fecha >= %s"
            params.append(filtros['fecha_desde'] + ' 00:00:00')
        if filtros.get('fecha_hasta'):
            sql += " AND i.fecha <= %s"
            params.append(filtros['fecha_hasta'] + ' 23:59:59')
        # Filtro por area responsable: existe una derivacion a esa area.
        if filtros.get('id_area'):
            sql += """ AND EXISTS (
                        SELECT 1 FROM incidencia_area ia
                        WHERE ia.id_incidencia = i.id AND ia.id_area = %s)"""
            params.append(filtros['id_area'])

        sql += " ORDER BY i.fecha DESC"

        cursor.execute(sql, params)
        resultado = cursor.fetchall()

        cursor.close()
        con.close()
        return resultado

    def obtener(self, incidencia_id):
        """Devuelve el detalle completo de una incidencia (o None si no existe)."""
        con = Conexion().open
        cursor = con.cursor()

        sql = """
            SELECT
                i.id,
                i.descripcion,
                c.nombre  AS categoria,
                ur.nombre AS urgencia,
                e.nombre  AS estado,
                i.id_estado,
                CONCAT(u.nombres, ' ', u.apellidos) AS reportante,
                u.correo_institucional AS reportante_correo,
                ub.nombre AS ubicacion,
                i.latitud,
                i.longitud,
                i.es_alerta_rapida,
                i.fecha
            FROM incidencia i
            LEFT JOIN categoria c  ON i.id_categoria = c.id
            LEFT JOIN urgencia ur  ON i.id_urgencia = ur.id
            INNER JOIN estado e    ON i.id_estado = e.id
            INNER JOIN usuario u   ON i.id_usuario = u.id
            LEFT JOIN ubicacion ub ON i.id_ubicacion = ub.id
            WHERE i.id = %s
        """
        cursor.execute(sql, [incidencia_id])
        resultado = cursor.fetchone()

        cursor.close()
        con.close()
        return resultado

    def listar_evidencias(self, incidencia_id):
        """Lista las imagenes (evidencias) adjuntas a la incidencia."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, url_imagen, creado_en FROM evidencia WHERE id_incidencia = %s ORDER BY id",
            [incidencia_id]
        )
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def linea_tiempo(self, incidencia_id):
        """
        Devuelve el historial de cambios de estado (linea de tiempo / trazabilidad).
        Incluye a que estado paso, a que area se derivo y quien hizo el cambio.
        """
        con = Conexion().open
        cursor = con.cursor()
        sql = """
            SELECT
                h.id,
                e.nombre AS estado,
                a.nombre AS area,
                CONCAT(u.nombres, ' ', u.apellidos) AS responsable,
                h.comentario,
                h.fecha
            FROM estado_incidencia h
            INNER JOIN estado e ON h.id_estado = e.id
            LEFT JOIN area a    ON h.id_area = a.id
            LEFT JOIN usuario u ON h.id_usuario = u.id
            WHERE h.id_incidencia = %s
            ORDER BY h.fecha ASC, h.id ASC
        """
        cursor.execute(sql, [incidencia_id])
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def derivaciones(self, incidencia_id):
        """Lista las areas a las que se ha derivado la incidencia."""
        con = Conexion().open
        cursor = con.cursor()
        sql = """
            SELECT a.nombre AS area, ia.fecha
            FROM incidencia_area ia
            INNER JOIN area a ON ia.id_area = a.id
            WHERE ia.id_incidencia = %s
            ORDER BY ia.fecha DESC
        """
        cursor.execute(sql, [incidencia_id])
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado

    def cambiar_estado(self, incidencia_id, id_estado, id_usuario, comentario=None):
        """
        Cambia el estado actual de la incidencia y deja registro en la linea
        de tiempo (trazabilidad). Las dos operaciones van juntas: si algo falla,
        se hace rollback para no dejar datos inconsistentes.
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            # 1) Actualizar el estado ACTUAL de la incidencia.
            cursor.execute(
                "UPDATE incidencia SET id_estado = %s WHERE id = %s",
                [id_estado, incidencia_id]
            )
            # 2) Registrar el cambio en el historial (quien y cuando).
            cursor.execute(
                """INSERT INTO estado_incidencia (id_incidencia, id_estado, id_usuario, comentario)
                   VALUES (%s, %s, %s, %s)""",
                [incidencia_id, id_estado, id_usuario, comentario]
            )
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            raise e
        finally:
            cursor.close()
            con.close()

    # ------------------------------------------------------------
    #  API MOVIL: registrar una incidencia (req. movil #4)
    # ------------------------------------------------------------
    def registrar_movil(self, descripcion, categoria_nombre, urgencia_nombre,
                        latitud, longitud, id_usuario, id_ubicacion, fecha=None):
        """
        Registra una incidencia enviada desde la app movil.
        La app manda la categoria y la urgencia por NOMBRE, asi que aqui las
        convertimos a su id buscando en los catalogos. El estado inicial es
        'Registrado' (id 1) y se deja la primera huella en la linea de tiempo.
        Devuelve (True, dict_incidencia) o (False, mensaje_error).
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            # Resolver el id de la categoria a partir de su nombre.
            id_categoria = None
            if categoria_nombre:
                cursor.execute("SELECT id FROM categoria WHERE nombre = %s", [categoria_nombre])
                fila = cursor.fetchone()
                id_categoria = fila['id'] if fila else None

            # Resolver el id de la urgencia a partir de su nombre.
            id_urgencia = None
            if urgencia_nombre:
                cursor.execute("SELECT id FROM urgencia WHERE nombre = %s", [urgencia_nombre])
                fila = cursor.fetchone()
                id_urgencia = fila['id'] if fila else None

            # id_ubicacion 0 (o vacio) se guarda como NULL.
            ubicacion = id_ubicacion if id_ubicacion else None

            # Insertar la incidencia con estado inicial 'Registrado' (id 1).
            # Si la app manda fecha la usamos; si no, la pone la BD (NOW()).
            if fecha:
                cursor.execute(
                    """INSERT INTO incidencia
                       (descripcion, id_categoria, id_urgencia, id_estado, id_usuario, id_ubicacion, latitud, longitud, fecha)
                       VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s)""",
                    [descripcion, id_categoria, id_urgencia, id_usuario, ubicacion, latitud, longitud, fecha]
                )
            else:
                cursor.execute(
                    """INSERT INTO incidencia
                       (descripcion, id_categoria, id_urgencia, id_estado, id_usuario, id_ubicacion, latitud, longitud)
                       VALUES (%s, %s, %s, 1, %s, %s, %s, %s)""",
                    [descripcion, id_categoria, id_urgencia, id_usuario, ubicacion, latitud, longitud]
                )
            nuevo_id = cursor.lastrowid

            # Primera huella en la linea de tiempo (trazabilidad).
            cursor.execute(
                """INSERT INTO estado_incidencia (id_incidencia, id_estado, id_usuario, comentario)
                   VALUES (%s, 1, %s, %s)""",
                [nuevo_id, id_usuario, 'Incidencia registrada desde la app movil']
            )

            con.commit()

            # Devolver la incidencia creada con los nombres de campo que espera
            # el modelo Incidencia de la app (categoria=id, urgencia=nombre, estado=id).
            incidencia_creada = {
                'id': nuevo_id,
                'descripcion': descripcion,
                'categoria': id_categoria,
                'urgencia': urgencia_nombre,
                'estado': 1,
                'latitud': latitud,
                'longitud': longitud,
                'id_usuario': id_usuario,
                'id_ubicacion': ubicacion or 0,
                'fecha': fecha or ''
            }
            return True, incidencia_creada
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            cursor.close()
            con.close()

    def derivar(self, incidencia_id, id_area, id_usuario, comentario=None):
        """
        Deriva la incidencia a un area responsable. Esto:
         1) registra la derivacion en incidencia_area,
         2) cambia el estado a 'Derivado' (id 3),
         3) deja la huella en la linea de tiempo con el area destino.
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            # 1) Registrar la derivacion (incidencia -> area).
            cursor.execute(
                "INSERT INTO incidencia_area (id_incidencia, id_area) VALUES (%s, %s)",
                [incidencia_id, id_area]
            )
            # 2) El estado pasa a 'Derivado' (id 3 en el catalogo 'estado').
            cursor.execute(
                "UPDATE incidencia SET id_estado = 3 WHERE id = %s",
                [incidencia_id]
            )
            # 3) Huella en la linea de tiempo, indicando el area destino.
            cursor.execute(
                """INSERT INTO estado_incidencia (id_incidencia, id_estado, id_area, id_usuario, comentario)
                   VALUES (%s, 3, %s, %s, %s)""",
                [incidencia_id, id_area, id_usuario, comentario]
            )
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            raise e
        finally:
            cursor.close()
            con.close()
