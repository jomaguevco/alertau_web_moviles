# ============================================================
#  routes/usuarios.py  -  Gestion de usuarios (req. web #6)
# ------------------------------------------------------------
#  Permite listar los usuarios del sistema y darlos de alta
#  (validar) o de baja (estado 1/0).
# ============================================================
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import Usuario
from tools.auth_required import login_requerido

ws_usuarios = Blueprint('ws_usuarios', __name__)

usuario = Usuario()


@ws_usuarios.route('/usuarios')
@login_requerido
def lista():
    """Lista todos los usuarios del sistema."""
    return render_template('usuarios/lista.html', usuarios=usuario.listar())


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
