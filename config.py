# ============================================================
#  config.py  -  Configuracion central de la aplicacion web
# ------------------------------------------------------------
#  Toda la configuracion se lee de VARIABLES DE ENTORNO.
#   - LOCAL : se cargan desde un archivo .env (ver .env.example)
#   - NUBE  : se definen en el panel del hosting (Railway, etc.)
#  De esta forma el codigo NO contiene contrasenas y el mismo
#  proyecto sirve para local y para produccion sin tocar nada.
# ============================================================
import os

# Cargar variables desde un archivo .env en desarrollo local (si existe).
# En produccion (Railway / Render / etc.) las variables se definen en el panel,
# por eso el import se hace dentro de un try (en la nube puede no estar python-dotenv).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _as_bool(valor):
    """Convierte un texto de variable de entorno ('true', '1', 'on'...) a booleano."""
    return str(valor).lower() in ('1', 'true', 'yes', 'on')


class Config:
    # --- Base de datos MySQL ---
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')          # XAMPP por defecto: root sin clave
    DB_NAME = os.environ.get('DB_NAME', 'incidencias_campus')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))

    # Activar SSL/TLS solo cuando el proveedor de BD lo exige (Aiven, TiDB, etc.).
    # En MySQL local (XAMPP) o en la red interna de Railway debe quedar en false.
    DB_SSL = _as_bool(os.environ.get('DB_SSL', 'false'))

    # Clave secreta usada por Flask para FIRMAR la cookie de sesion del login web
    # y tambien para firmar los tokens JWT de la API movil.
    # En produccion conviene cambiarla por una variable de entorno propia.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ALERTAU2026$$**campus')

    # --- Correo (SMTP) para la recuperacion de contrasena (req. movil #3) ---
    # Se definen como variables de entorno (en Railway o en .env). Si no se
    # configuran, la API igual genera el codigo pero no envia el correo.
    SMTP_HOST = os.environ.get('SMTP_HOST', '')                 # ej. smtp.gmail.com
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))           # 587 = TLS
    SMTP_USER = os.environ.get('SMTP_USER', '')                 # tu correo
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')         # contrasena de aplicacion
    SMTP_FROM = os.environ.get('SMTP_FROM', '') or SMTP_USER    # remitente mostrado
