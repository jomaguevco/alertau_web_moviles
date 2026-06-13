# ============================================================
#  models/catalogo.py  -  Acceso a datos de los CATALOGOS
# ------------------------------------------------------------
#  Los catalogos son las tablas maestras (listas fijas) que se
#  usan para llenar los <select> de los filtros y formularios:
#  categorias, niveles de urgencia, estados y areas.
# ============================================================
from conexionBD import Conexion


class Catalogo:

    def categorias(self):
        """Lista de categorias (emergencia medica, seguridad, etc.).
        Incluye 'estado' porque la app movil lo espera en su modelo Categoria."""
        return self._listar_simple("SELECT id, nombre, estado FROM categoria WHERE estado = 1 ORDER BY id")

    def urgencias(self):
        """Lista de niveles de urgencia (baja, media, alta, critica)."""
        return self._listar_simple("SELECT id, nombre, estado FROM urgencia WHERE estado = 1 ORDER BY id")

    def estados(self):
        """Lista de estados del flujo (registrado, en revision, ...)."""
        return self._listar_simple("SELECT id, nombre FROM estado WHERE estado = 1 ORDER BY id")

    def areas(self):
        """Lista de areas responsables a las que se deriva una incidencia."""
        return self._listar_simple("SELECT id, nombre FROM area WHERE estado = 1 ORDER BY id")

    def tipos_usuario(self):
        """Lista de tipos/roles de usuario (para el combo de registro en la app movil)."""
        return self._listar_simple("SELECT id, nombre, estado FROM tipo_usuario WHERE estado = 1 ORDER BY id")

    def _listar_simple(self, sql):
        """Metodo interno reutilizable: ejecuta un SELECT y devuelve todas las filas."""
        con = Conexion().open
        cursor = con.cursor()
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()
        con.close()
        return resultado
