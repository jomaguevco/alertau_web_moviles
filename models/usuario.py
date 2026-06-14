# ============================================================
#  models/usuario.py  -  Acceso a datos de USUARIOS
# ------------------------------------------------------------
#  Contiene las consultas SQL relacionadas a usuarios:
#   - login()          : buscar usuario por correo (para iniciar sesion)
#   - listar()         : listado para la pantalla "Gestion de usuarios"
#   - cambiar_estado() : dar de alta/baja (validar) un usuario
# ============================================================
import secrets
from datetime import datetime, timedelta
from conexionBD import Conexion
from tools.security import hash_password


class Usuario:

    def login(self, correo):
        """
        Busca un usuario por su correo institucional y devuelve sus datos
        (incluido el hash de la contrasena, que la ruta usara para verificar).
        Devuelve None si el correo no existe.
        """
        con = Conexion().open
        cursor = con.cursor()

        # Traemos tambien el nombre del rol y el id del tipo de usuario,
        # porque al panel web SOLO puede entrar el personal autorizado
        # (Administrativo = 3, Personal autorizado = 4).
        sql = """
            SELECT
                u.id                AS usuario_id,
                u.nombres,
                u.apellidos,
                u.correo_institucional,
                u.dni,
                u.telefono,
                u.imagen,
                u.contrasenia,
                u.id_tipo_usuario,
                t.nombre            AS rol,
                u.estado
            FROM usuario u
            INNER JOIN tipo_usuario t ON u.id_tipo_usuario = t.id
            WHERE u.correo_institucional = %s
        """
        cursor.execute(sql, [correo])
        resultado = cursor.fetchone()

        cursor.close()
        con.close()
        return resultado

    def listar(self):
        """Lista todos los usuarios para la pantalla de gestion de usuarios."""
        con = Conexion().open
        cursor = con.cursor()

        sql = """
            SELECT
                u.id,
                CONCAT(u.nombres, ' ', u.apellidos) AS nombre,
                u.correo_institucional,
                u.dni,
                u.telefono,
                t.nombre AS rol,
                u.estado
            FROM usuario u
            INNER JOIN tipo_usuario t ON u.id_tipo_usuario = t.id
            ORDER BY u.id;
        """
        cursor.execute(sql)
        resultado = cursor.fetchall()

        cursor.close()
        con.close()
        return resultado

    def cambiar_estado(self, usuario_id, nuevo_estado):
        """
        Da de alta (estado=1) o de baja (estado=0) a un usuario.
        Sirve para el requerimiento web #6 (alta/baja o validacion de usuarios).
        """
        con = Conexion().open
        cursor = con.cursor()

        sql = "UPDATE usuario SET estado = %s WHERE id = %s"
        cursor.execute(sql, [nuevo_estado, usuario_id])
        con.commit()

        cursor.close()
        con.close()
        return True

    # ------------------------------------------------------------
    #  API MOVIL: registro de usuario (req. movil #1)
    # ------------------------------------------------------------
    def registrar(self, nombres, apellidos, correo, dni, telefono, tipo_usuario, contrasenia):
        """
        Registra un nuevo usuario desde la app movil.
        Devuelve (True, id_nuevo) si se creo, o (False, mensaje_error) si no.
        La contrasena se guarda hasheada con argon2.
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            # No permitir correos ni DNIs duplicados (son UNIQUE en la BD).
            cursor.execute("SELECT id FROM usuario WHERE correo_institucional = %s", [correo])
            if cursor.fetchone():
                return False, "El correo ya esta registrado"

            cursor.execute("SELECT id FROM usuario WHERE dni = %s", [dni])
            if cursor.fetchone():
                return False, "El DNI ya esta registrado"

            cursor.execute(
                """INSERT INTO usuario
                   (nombres, apellidos, correo_institucional, dni, telefono, id_tipo_usuario, contrasenia, estado)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 1)""",
                [nombres, apellidos, correo, dni, telefono, tipo_usuario, hash_password(contrasenia)]
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

    # ------------------------------------------------------------
    #  API MOVIL: perfil del usuario (req. movil #12)
    # ------------------------------------------------------------
    def obtener_perfil(self, usuario_id):
        """Devuelve los datos de perfil de un usuario (para ver/editar en la app)."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            """SELECT
                   id, nombres, apellidos, correo_institucional, dni, telefono,
                   id_tipo_usuario AS tipo_usuario, imagen, estado,
                   COALESCE(contacto_emergencia_nombre, '')   AS contacto_emergencia_nombre,
                   COALESCE(contacto_emergencia_telefono, '') AS contacto_emergencia_telefono
               FROM usuario WHERE id = %s""",
            [usuario_id]
        )
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        return resultado

    def actualizar_perfil(self, usuario_id, nombres, apellidos, telefono,
                          contacto_nombre, contacto_telefono):
        """Actualiza los datos editables del perfil (req. #12)."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            """UPDATE usuario
               SET nombres = %s, apellidos = %s, telefono = %s,
                   contacto_emergencia_nombre = %s, contacto_emergencia_telefono = %s
               WHERE id = %s""",
            [nombres, apellidos, telefono, contacto_nombre, contacto_telefono, usuario_id]
        )
        con.commit()
        cursor.close()
        con.close()
        return True

    def actualizar_foto(self, usuario_id, nombre_archivo):
        """Guarda el nombre del archivo de la foto de perfil."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute("UPDATE usuario SET imagen = %s WHERE id = %s", [nombre_archivo, usuario_id])
        con.commit()
        cursor.close()
        con.close()
        return True

    def guardar_fcm_token(self, usuario_id, token):
        """Guarda el token de Firebase del dispositivo para enviar notificaciones push (req. #9)."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute("UPDATE usuario SET fcm_token = %s WHERE id = %s", [token, usuario_id])
        con.commit()
        cursor.close()
        con.close()
        return True

    def fcm_token_de_incidencia(self, id_incidencia):
        """Obtiene el fcm_token del usuario que reporto una incidencia (para enviarle push)."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(
            """SELECT u.id AS id_usuario, u.fcm_token
               FROM incidencia i INNER JOIN usuario u ON i.id_usuario = u.id
               WHERE i.id = %s""",
            [id_incidencia]
        )
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        return resultado

    # ------------------------------------------------------------
    #  API MOVIL: recuperacion de contrasena (req. movil #3)
    # ------------------------------------------------------------
    def crear_codigo_recuperacion(self, correo, minutos_validez=15):
        """
        Genera un codigo de recuperacion para el correo dado y lo guarda en la
        tabla recuperacion_contrasenia. Devuelve (correo, nombres, codigo) si el
        usuario existe, o None si el correo no esta registrado.
        El envio del correo lo hace la ruta (tools/email_util.py).
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            cursor.execute(
                "SELECT id, nombres FROM usuario WHERE correo_institucional = %s",
                [correo]
            )
            usuario = cursor.fetchone()
            if not usuario:
                return None

            # Codigo de 6 digitos (secrets = aleatorio seguro).
            codigo = f"{secrets.randbelow(1000000):06d}"
            expira = datetime.now() + timedelta(minutes=minutos_validez)

            cursor.execute(
                """INSERT INTO recuperacion_contrasenia (id_usuario, codigo, expira_en)
                   VALUES (%s, %s, %s)""",
                [usuario['id'], codigo, expira.strftime('%Y-%m-%d %H:%M:%S')]
            )
            con.commit()
            return {'correo': correo, 'nombres': usuario['nombres'], 'codigo': codigo}
        except Exception as e:
            con.rollback()
            raise e
        finally:
            cursor.close()
            con.close()

    def cambiar_contrasenia_con_codigo(self, correo, codigo, nueva_contrasenia):
        """
        Valida el codigo de recuperacion y, si es correcto y no expiro, cambia la
        contrasena del usuario. Devuelve (True, mensaje) o (False, mensaje).
        """
        con = Conexion().open
        cursor = con.cursor()
        try:
            cursor.execute("SELECT id FROM usuario WHERE correo_institucional = %s", [correo])
            usuario = cursor.fetchone()
            if not usuario:
                return False, "Correo no registrado"

            # Buscar un codigo valido: no usado y no expirado.
            cursor.execute(
                """SELECT id FROM recuperacion_contrasenia
                   WHERE id_usuario = %s AND codigo = %s AND usado = 0 AND expira_en > NOW()
                   ORDER BY id DESC LIMIT 1""",
                [usuario['id'], codigo]
            )
            recuperacion = cursor.fetchone()
            if not recuperacion:
                return False, "Codigo invalido o expirado"

            # Actualizar la contrasena (hash argon2) y marcar el codigo como usado.
            cursor.execute(
                "UPDATE usuario SET contrasenia = %s WHERE id = %s",
                [hash_password(nueva_contrasenia), usuario['id']]
            )
            cursor.execute(
                "UPDATE recuperacion_contrasenia SET usado = 1 WHERE id = %s",
                [recuperacion['id']]
            )
            con.commit()
            return True, "Contrasena actualizada correctamente"
        except Exception as e:
            con.rollback()
            return False, str(e)
        finally:
            cursor.close()
            con.close()
