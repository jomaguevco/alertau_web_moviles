# ============================================================
#  routes/usuarios.py  -  Gestion de usuarios (req. web #6)
# ------------------------------------------------------------
#  Permite listar los usuarios del sistema y darlos de alta
#  (validar) o de baja (estado 1/0).
# ============================================================
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import Usuario
from models.catalogo import Catalogo
from tools.auth_required import login_requerido

ws_usuarios = Blueprint('ws_usuarios', __name__)

usuario = Usuario()
catalogo = Catalogo()


@ws_usuarios.route('/usuarios')
@login_requerido
def lista():
    """Lista todos los usuarios del sistema y permite dar de alta uno nuevo."""
    return render_template('usuarios/lista.html',
                           usuarios=usuario.listar(),
                           tipos=catalogo.tipos_usuario())


@ws_usuarios.route('/usuarios/nuevo', methods=['POST'])
@login_requerido
def nuevo():
    """Alta de un usuario desde el panel web (req. #6)."""
    f = request.form
    if not all([f.get('nombres'), f.get('apellidos'), f.get('correo'),
                f.get('dni'), f.get('tipo_usuario'), f.get('contrasenia')]):
        flash('Completa todos los campos obligatorios.', 'danger')
        return redirect(url_for('ws_usuarios.lista'))

    exitoso, resultado = usuario.registrar(
        f.get('nombres'), f.get('apellidos'), f.get('correo'), f.get('dni'),
        f.get('telefono'), f.get('tipo_usuario'), f.get('contrasenia')
    )
    if exitoso:
        flash('Usuario creado correctamente.', 'success')
    else:
        flash('No se pudo crear: ' + str(resultado), 'danger')
    return redirect(url_for('ws_usuarios.lista'))


@ws_usuarios.route('/usuarios/<int:id_usuario>/estado', methods=['POST'])
@login_requerido
def cambiar_estado(id_usuario):
    """
    Cambia el estado de un usuario (alta/baja).
    El formulario envia el nuevo estado deseado (1 = activo, 0 = inactivo).
    """
    nuevo_estado = request.form.get('nuevo_estado')

    # No permitir que el usuario se desactive a si mismo (evita quedarse fuera).
    if id_usuario == session.get('usuario_id'):
        flash('No puedes cambiar el estado de tu propia cuenta.', 'warning')
        return redirect(url_for('ws_usuarios.lista'))

    usuario.cambiar_estado(id_usuario, nuevo_estado)
    flash('Estado del usuario actualizado.', 'success')
    return redirect(url_for('ws_usuarios.lista'))
