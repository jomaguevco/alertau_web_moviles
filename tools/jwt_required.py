# ============================================================
#  tools/jwt_required.py  -  Proteger endpoints de la API con JWT
# ------------------------------------------------------------
#  Decorador para las rutas de la API movil que exigen un token
#  valido. Lee la cabecera Authorization: Bearer <token>, lo
#  valida y guarda el usuario_id en request para usarlo en la ruta.
#
#  (Para el panel WEB se usa la sesion; ver tools/auth_required.py.)
# ============================================================
from functools import wraps
from flask import request, jsonify
from tools.jwt_utils import verificar_token


def jwt_token_requerido(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization")
        if not cabecera:
            return jsonify({'data': None, 'message': 'Cabecera de autorizacion no valida', 'status': 0}), 401

        # La cabecera viene como "Bearer <token>": nos quedamos con el token.
        partes = cabecera.split('Bearer ')
        token = partes[1] if len(partes) > 1 else None
        if not token:
            return jsonify({'data': None, 'message': 'Token requerido', 'status': 0}), 401

        payload = verificar_token(token)
        if not payload:
            return jsonify({'data': None, 'message': 'Token invalido o expirado', 'status': 0}), 401

        # Guardar el id del usuario autenticado para usarlo dentro de la ruta.
        request.usuario_id = payload.get('usuario_id')
        return f(*args, **kwargs)
    return envoltura
