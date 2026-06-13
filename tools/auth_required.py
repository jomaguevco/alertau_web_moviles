# ============================================================
#  tools/auth_required.py  -  Control de acceso por SESION
# ------------------------------------------------------------
#  En la app movil la seguridad se hace con tokens JWT. Aqui,
#  al ser un panel WEB renderizado en el servidor, usamos la
#  SESION de Flask (una cookie firmada): cuando el personal
#  inicia sesion guardamos su id, nombre y rol en session.
#
#  El decorador 'login_requerido' se pone encima de cada ruta
#  que requiere haber iniciado sesion. Si no hay sesion, redirige
#  al login.
# ============================================================
from functools import wraps
from flask import session, redirect, url_for, flash


def login_requerido(f):
    """Protege una ruta: solo accesible si hay una sesion iniciada."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        # 'usuario_id' se guarda en la sesion al iniciar sesion (ver routes/auth.py).
        if 'usuario_id' not in session:
            flash('Debes iniciar sesion para acceder al panel.', 'warning')
            return redirect(url_for('ws_auth.login'))
        return f(*args, **kwargs)
    return envoltura
