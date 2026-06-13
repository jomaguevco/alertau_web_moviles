# ============================================================
#  conexionBD.py  -  Conexion a la base de datos MySQL
# ------------------------------------------------------------
#  Encapsula la apertura de la conexion a MySQL usando los
#  datos de config.py. Se usa asi en los models:
#
#       con = Conexion().open
#       cursor = con.cursor()
#       ...
#       cursor.close(); con.close()
# ============================================================
# Usamos PyMySQL (Python puro) pero lo registramos con el nombre 'MySQLdb'
# para que el resto del codigo se escriba EXACTAMENTE igual que con el driver
# clasico (import MySQLdb). Asi evitamos necesitar un compilador de C en Windows.
import pymysql
pymysql.install_as_MySQLdb()

import MySQLdb as dbc
import MySQLdb.cursors
from config import Config


class Conexion:
    def __init__(self):
        # Parametros de conexion. cursorclass=DictCursor hace que cada fila
        # se devuelva como un diccionario {columna: valor} en lugar de una tupla,
        # lo que facilita leer los resultados por nombre de columna.
        kwargs = dict(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            passwd=Config.DB_PASSWORD,
            db=Config.DB_NAME,
            port=Config.DB_PORT,
            cursorclass=dbc.cursors.DictCursor,
            # Forzar UTF-8 para que los acentos y la enie se lean/escriban bien
            # (sin esto, "Infraestructura" o "Critica" podrian verse mal).
            charset='utf8mb4',
            use_unicode=True
        )

        # Proveedores como Aiven o TiDB exigen conexion cifrada (TLS).
        # En PyMySQL se activa TLS pasando un dict 'ssl' (vacio fuerza el
        # cifrado sin exigir certificado CA). En MySQL local debe quedar en false.
        if Config.DB_SSL:
            kwargs['ssl'] = {'ssl': {}}

        self.dblink = dbc.connect(**kwargs)

    @property
    def open(self):
        """Devuelve la conexion abierta lista para crear cursores."""
        return self.dblink
