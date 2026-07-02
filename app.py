# ============================================================
#  app.py  -  Punto de entrada de la aplicacion web AlertaU
# ------------------------------------------------------------
#  Panel web para el PERSONAL AUTORIZADO del campus (seccion 4
#  del documento del proyecto). Permite: iniciar sesion, ver un
#  panel resumen, gestionar incidencias (filtrar, ver detalle,
#  cambiar estado, derivar a un area, ver evidencias, responder
#  por chat) y gestionar usuarios.
#
#  Arquitectura (igual filosofia que la API movil, ver README):
#       app.py        -> arranca Flask y registra los blueprints
#       config.py     -> configuracion por variables de entorno
#       conexionBD.py -> conexion a MySQL
#       models/       -> acceso a datos (consultas SQL)
#       routes/       -> endpoints / paginas (blueprints)
#       tools/        -> seguridad (argon2) y control de sesion
#       templates/    -> vistas HTML (Jinja2 + Bootstrap)
#       static/       -> css y js del frontend
#       uploads/      -> imagenes (evidencias y fotos de usuario)
# ============================================================
import os
from flask import Flask, redirect, url_for

# Importar los blueprints (cada uno agrupa un conjunto de rutas)
from routes.auth import ws_auth
from routes.dashboard import ws_dashboard
from routes.incidencias import ws_incidencias
from routes.usuarios import ws_usuarios
from routes.reportes import ws_reportes
from routes.api import ws_api
from config import Config

app = Flask(__name__)

# Clave secreta para firmar la cookie de sesion (login del personal).
app.secret_key = Config.SECRET_KEY

# Registrar los blueprints. Al ser un panel web (no una API), las rutas
# viven en la raiz del sitio (sin el prefijo /api que usa la app movil).
app.register_blueprint(ws_auth)
app.register_blueprint(ws_dashboard)
app.register_blueprint(ws_incidencias)
app.register_blueprint(ws_usuarios)
app.register_blueprint(ws_reportes)

# API REST JSON para la app movil (bajo el prefijo /api). El panel web sigue
# usando las rutas de arriba con sesion; esta capa usa JWT y devuelve JSON.
app.register_blueprint(ws_api, url_prefix='/api')


# Pagina raiz: redirige al login (o al panel si ya hay sesion, lo decide /login).
@app.route('/')
def home():
    return redirect(url_for('ws_auth.login'))


# Arranque del servidor web con Flask (solo para ejecucion LOCAL).
# En produccion lo arranca gunicorn (ver Procfile).
if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 3007))
    # debug se activa SOLO si defines FLASK_DEBUG=1. Por defecto queda apagado
    # para no exponer el debugger de Werkzeug ni mostrar trazas de error al
    # usuario (importante en una demostracion). Para desarrollar: FLASK_DEBUG=1.
    modo_debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(port=puerto, debug=modo_debug, host='0.0.0.0')
