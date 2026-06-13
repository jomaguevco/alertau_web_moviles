# ============================================================
#  routes/auth.py  -  Inicio y cierre de sesion (req. web #1)
# ------------------------------------------------------------
#  Al panel web SOLO pueden entrar el personal autorizado:
#  Administrativo (tipo 3) y Personal autorizado (tipo 4).
#  Los estudiantes y docentes usaran la app movil.
# ============================================================
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import Usuario
from tools.security import verificar_password

ws_auth = Blueprint('ws_auth', __name__)

usuario = Usuario()

# Tipos de usuario que tienen permiso para entrar al panel web.
TIPOS_PERMITIDOS_WEB = (3, 4)   # 3=Administrativo, 4=Personal autorizado


@ws_auth.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay sesion iniciada, ir directo al panel.
    if 'usuario_id' in session:
        return redirect(url_for('ws_dashboard.dashboard'))

    # GET: mostrar el formulario de login.
    if request.method == 'GET':
        return render_template('login.html')

    # POST: procesar las credenciales enviadas por el formulario.
    correo = request.form.get('correo', '').strip()
    password = request.form.get('password', '')

    # Validar que llegaron ambos campos.
    if not correo or not password:
        flash('Debes ingresar correo y contrasena.', 'danger')
        return redirect(url_for('ws_auth.login'))

    # Buscar al usuario por su correo.
    datos = usuario.login(correo)

    # 1) El correo no existe.
    if not datos:
        flash('Credenciales incorrectas.', 'danger')
        return redirect(url_for('ws_auth.login'))

    # 2) La contrasena no coincide con el hash guardado.
    if not verificar_password(datos['contrasenia'], password):
        flash('Credenciales incorrectas.', 'danger')
        return redirect(url_for('ws_auth.login'))

    # 3) El usuario no es personal autorizado (es estudiante o docente).
    if datos['id_tipo_usuario'] not in TIPOS_PERMITIDOS_WEB:
        flash('Este panel es solo para el personal autorizado del campus.', 'warning')
        return redirect(url_for('ws_auth.login'))

    # 4) El usuario esta dado de baja (estado = 0).
    if datos['estado'] != 1:
        flash('Tu cuenta esta inactiva. Contacta al administrador.', 'warning')
        return redirect(url_for('ws_auth.login'))

    # Todo correcto: guardamos los datos en la sesion (cookie firmada).
    session['usuario_id'] = datos['usuario_id']
    session['nombre'] = f"{datos['nombres']} {datos['apellidos']}"
    session['rol'] = datos['rol']

    flash('Bienvenido(a), ' + datos['nombres'] + '.', 'success')
    return redirect(url_for('ws_dashboard.dashboard'))


@ws_auth.route('/logout')
def logout():
    # Vaciar la sesion para cerrar sesion.
    session.clear()
    flash('Has cerrado sesion correctamente.', 'success')
    return redirect(url_for('ws_auth.login'))
