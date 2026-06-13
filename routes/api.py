# ============================================================
#  routes/api.py  -  API REST JSON para la APP MOVIL
# ------------------------------------------------------------
#  Estos endpoints son los que consume la aplicacion Android
#  (Retrofit). Van bajo el prefijo /api y devuelven SIEMPRE el
#  mismo formato que la app espera:
#
#       { "data": ..., "message": "...", "status": <entero> }
#
#  status: 1 = ok, 0 = error (asi lo interpreta la app).
#  El login ademas devuelve "access_token" (JWT).
#
#  IMPORTANTE: este blueprint NO toca el panel web (sesion);
#  es la capa para movil con JWT, separada y documentada.
# ============================================================
from flask import Blueprint, request, jsonify
from models.usuario import Usuario
from models.incidencia import Incidencia
from models.catalogo import Catalogo
from tools.security import verificar_password
from tools.jwt_utils import generar_token
from tools.email_util import enviar_correo

ws_api = Blueprint('ws_api', __name__)

usuario = Usuario()
incidencia = Incidencia()
catalogo = Catalogo()


# ----------------------------------------------------------
#  POST /api/auth/usuario  -> Login (req. movil #2)
#  Recibe: { correo_institucional, contrasenia }
#  Devuelve: { data: usuario, access_token, message, status }
# ----------------------------------------------------------
@ws_api.route('/auth/usuario', methods=['POST'])
def auth_usuario():
    data = request.get_json(silent=True) or {}
    correo = data.get('correo_institucional')
    contrasenia = data.get('contrasenia')

    if not correo or not contrasenia:
        return jsonify({'data': None, 'access_token': None,
                        'message': 'Faltan datos obligatorios', 'status': 0}), 400

    fila = usuario.login(correo)

    # Correo inexistente o contrasena incorrecta -> credenciales invalidas.
    if not fila or not verificar_password(fila['contrasenia'], contrasenia):
        return jsonify({'data': None, 'access_token': None,
                        'message': 'Credenciales incorrectas', 'status': 0}), 401

    # Construir el usuario con los nombres de campo que espera el modelo de la app
    # (tipo_usuario = id del rol; NO devolvemos la contrasena).
    usuario_data = {
        'id': fila['usuario_id'],
        'nombres': fila['nombres'],
        'apellidos': fila['apellidos'],
        'correo_institucional': fila['correo_institucional'],
        'dni': fila['dni'],
        'telefono': fila['telefono'],
        'tipo_usuario': fila['id_tipo_usuario'],
        'contrasenia': None,
        'estado': fila['estado'],
        'imagen': fila['imagen'],
    }

    # Generar el token JWT (vive 1 hora) con el id del usuario.
    token = generar_token({'usuario_id': fila['usuario_id']}, 60 * 60)

    return jsonify({
        'data': usuario_data,
        'access_token': token,
        'message': 'Inicio de sesion satisfactorio',
        'status': 1
    }), 200


# ----------------------------------------------------------
#  GET /api/listarTiposUsuario  -> roles para el registro
# ----------------------------------------------------------
@ws_api.route('/listarTiposUsuario', methods=['GET'])
def listar_tipos_usuario():
    try:
        tipos = catalogo.tipos_usuario()
        return jsonify({'data': tipos, 'message': 'Tipos de usuario obtenidos', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/registrarUsuario  -> Registro (req. movil #1)
#  Recibe el modelo Usuario de la app.
# ----------------------------------------------------------
@ws_api.route('/registrarUsuario', methods=['POST'])
def registrar_usuario():
    data = request.get_json(silent=True) or {}

    nombres = data.get('nombres')
    apellidos = data.get('apellidos')
    correo = data.get('correo_institucional')
    dni = data.get('dni')
    telefono = data.get('telefono')
    tipo_usuario = data.get('tipo_usuario')
    contrasenia = data.get('contrasenia')

    if not all([nombres, apellidos, correo, dni, tipo_usuario, contrasenia]):
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400

    exitoso, resultado = usuario.registrar(nombres, apellidos, correo, dni, telefono, tipo_usuario, contrasenia)

    if not exitoso:
        return jsonify({'data': None, 'message': resultado, 'status': 0}), 400

    # 'resultado' es el id del nuevo usuario. Devolvemos el usuario creado.
    usuario_data = {
        'id': resultado,
        'nombres': nombres,
        'apellidos': apellidos,
        'correo_institucional': correo,
        'dni': dni,
        'telefono': telefono,
        'tipo_usuario': tipo_usuario,
        'contrasenia': None,
        'estado': 1,
        'imagen': None,
    }
    return jsonify({'data': usuario_data, 'message': 'Usuario registrado correctamente', 'status': 1}), 201


# ----------------------------------------------------------
#  POST /api/recuperarContraseniaUsuario  -> (req. movil #3)
#  Recibe: { email }. Genera un codigo y lo envia por correo.
# ----------------------------------------------------------
@ws_api.route('/recuperarContraseniaUsuario', methods=['POST'])
def recuperar_contrasenia():
    data = request.get_json(silent=True) or {}
    correo = data.get('email')

    if not correo:
        return jsonify({'data': None, 'message': 'Falta el correo', 'status': 0}), 400

    try:
        info = usuario.crear_codigo_recuperacion(correo)
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500

    # Por seguridad, si el correo no existe respondemos sin revelar detalles.
    if not info:
        return jsonify({'data': None, 'message': 'Correo no registrado', 'status': 0}), 404

    # Intentar enviar el codigo por correo (si SMTP esta configurado).
    cuerpo = (f"Hola {info['nombres']},\n\n"
              f"Tu codigo de recuperacion de contrasena es: {info['codigo']}\n"
              f"Vence en 15 minutos.\n\nAlertaU - Campus Universitario")
    enviado = enviar_correo(info['correo'], 'Recuperacion de contrasena - AlertaU', cuerpo)

    mensaje = ('Se envio un codigo de recuperacion a tu correo'
               if enviado else
               'Codigo generado (configura SMTP para enviarlo por correo)')
    return jsonify({'data': None, 'message': mensaje, 'status': 1}), 200


# ----------------------------------------------------------
#  GET /api/categorias  -> categorias (req. movil #5)
# ----------------------------------------------------------
@ws_api.route('/categorias', methods=['GET'])
def listar_categorias():
    try:
        return jsonify({'data': catalogo.categorias(), 'message': 'Categorias obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/urgencias  -> niveles de urgencia
# ----------------------------------------------------------
@ws_api.route('/urgencias', methods=['GET'])
def listar_urgencias():
    try:
        return jsonify({'data': catalogo.urgencias(), 'message': 'Urgencias obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/registrarIncidencia  -> reportar (req. movil #4)
#  Recibe el modelo RegistrarIncidenciaRequest de la app.
# ----------------------------------------------------------
@ws_api.route('/registrarIncidencia', methods=['POST'])
def registrar_incidencia():
    data = request.get_json(silent=True) or {}

    descripcion = data.get('descripcion')
    categoria = data.get('categoria')        # nombre de la categoria
    urgencia = data.get('urgencia')          # nombre de la urgencia
    latitud = data.get('latitud')
    longitud = data.get('longitud')
    id_usuario = data.get('id_usuario')
    id_ubicacion = data.get('id_ubicacion')
    fecha = data.get('fecha')

    if not descripcion or not id_usuario:
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400

    exitoso, resultado = incidencia.registrar_movil(
        descripcion, categoria, urgencia, latitud, longitud, id_usuario, id_ubicacion, fecha
    )

    if not exitoso:
        return jsonify({'data': None, 'message': resultado, 'status': 0}), 400

    return jsonify({'data': resultado, 'message': 'Incidencia registrada correctamente', 'status': 1}), 201
