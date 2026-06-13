# ============================================================
#  models/usuario.py  -  Acceso a datos de USUARIOS
# ------------------------------------------------------------
#  Contiene las consultas SQL relacionadas a usuarios:
#   - login()          : buscar usuario por correo (para iniciar sesion)
#   - listar()         : listado para la pantalla "Gestion de usuarios"
#   - cambiar_estado() : dar de alta/baja (validar) un usuario
# ============================================================
from conexionBD import Conexion


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
