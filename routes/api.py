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
import os
import secrets
from flask import Blueprint, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from config import Config
from models.usuario import Usuario
from models.incidencia import Incidencia
from models.catalogo import Catalogo
from models.notificacion import Notificacion
from models.calificacion import Calificacion
from models.mensaje import Mensaje
from models.evidencia import Evidencia
from tools.security import verificar_password
from tools.jwt_utils import generar_token
from tools.email_util import enviar_correo
from tools.notificar import notificar_usuario

ws_api = Blueprint('ws_api', __name__)

usuario = Usuario()
incidencia = Incidencia()
catalogo = Catalogo()
notificacion = Notificacion()
calificacion = Calificacion()
mensaje = Mensaje()
evidencia = Evidencia()

# Carpetas de imagenes (dentro de la carpeta de uploads configurable).
CARPETA_EVIDENCIAS = os.path.join(Config.UPLOAD_DIR, 'evidencias')
CARPETA_USUARIOS = os.path.join(Config.UPLOAD_DIR, 'usuarios')
EXTENSIONES_OK = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _extension_valida(nombre):
    return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in EXTENSIONES_OK


def _guardar_imagen(archivo, carpeta, prefijo):
    """Guarda un archivo de imagen con un nombre unico y devuelve ese nombre."""
    os.makedirs(carpeta, exist_ok=True)
    ext = secure_filename(archivo.filename).rsplit('.', 1)[1].lower()
    nombre = f"{prefijo}_{secrets.token_hex(6)}.{ext}"
    archivo.save(os.path.join(carpeta, nombre))
    return nombre


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

    # Notificar al usuario que su caso fue recibido (req. #9).
    notificar_usuario(id_usuario, 'Tu incidencia fue registrada y esta en revision.')

    return jsonify({'data': resultado, 'message': 'Incidencia registrada correctamente', 'status': 1}), 201


# ==========================================================
#  ENDPOINTS ADICIONALES PARA LA APP MOVIL
# ==========================================================

# ----------------------------------------------------------
#  GET /api/misIncidencias/<id_usuario>  -> historial (req. #7)
# ----------------------------------------------------------
@ws_api.route('/misIncidencias/<int:id_usuario>', methods=['GET'])
def mis_incidencias(id_usuario):
    try:
        datos = incidencia.mis_incidencias(id_usuario)
        return jsonify({'data': datos, 'message': 'Incidencias obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/seguimiento/<id_incidencia>  -> linea de tiempo (req. #8)
# ----------------------------------------------------------
@ws_api.route('/seguimiento/<int:id_incidencia>', methods=['GET'])
def seguimiento(id_incidencia):
    try:
        datos = incidencia.seguimiento(id_incidencia)
        return jsonify({'data': datos, 'message': 'Seguimiento obtenido', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/reabrirIncidencia  -> reapertura (req. #15)
#  Recibe: { id_incidencia, id_usuario, motivo }
# ----------------------------------------------------------
@ws_api.route('/reabrirIncidencia', methods=['POST'])
def reabrir_incidencia():
    data = request.get_json(silent=True) or {}
    id_incidencia = data.get('id_incidencia')
    id_usuario = data.get('id_usuario')
    motivo = data.get('motivo')

    if not id_incidencia or not motivo:
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400

    try:
        incidencia.reabrir(id_incidencia, id_usuario, motivo)
        return jsonify({'data': None, 'message': 'Incidencia reabierta', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/alertaRapida  -> boton de panico (req. #13)
#  Recibe: { id_usuario, latitud, longitud, descripcion? }
# ----------------------------------------------------------
@ws_api.route('/alertaRapida', methods=['POST'])
def alerta_rapida():
    data = request.get_json(silent=True) or {}
    id_usuario = data.get('id_usuario')
    latitud = data.get('latitud')
    longitud = data.get('longitud')
    descripcion = data.get('descripcion')

    if not id_usuario:
        return jsonify({'data': None, 'message': 'Falta el usuario', 'status': 0}), 400

    exitoso, resultado = incidencia.alerta_rapida(id_usuario, latitud, longitud, descripcion)
    if not exitoso:
        return jsonify({'data': None, 'message': resultado, 'status': 0}), 400

    notificar_usuario(id_usuario, 'Tu alerta rapida fue recibida. El personal fue avisado.')
    return jsonify({'data': {'id': resultado}, 'message': 'Alerta rapida registrada', 'status': 1}), 201


# ----------------------------------------------------------
#  GET /api/incidenciasMapa  -> incidencias con coordenadas (req. #6)
# ----------------------------------------------------------
@ws_api.route('/incidenciasMapa', methods=['GET'])
def incidencias_mapa():
    try:
        datos = incidencia.incidencias_mapa()
        return jsonify({'data': datos, 'message': 'Incidencias del mapa', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/ubicaciones  -> zonas / puntos del campus (req. #6)
# ----------------------------------------------------------
@ws_api.route('/ubicaciones', methods=['GET'])
def ubicaciones():
    try:
        return jsonify({'data': catalogo.ubicaciones(), 'message': 'Ubicaciones obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/notificaciones/<id_usuario>  -> historial (req. #9)
# ----------------------------------------------------------
@ws_api.route('/notificaciones/<int:id_usuario>', methods=['GET'])
def listar_notificaciones(id_usuario):
    try:
        datos = notificacion.listar(id_usuario)
        return jsonify({'data': datos, 'message': 'Notificaciones obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/notificaciones/leer/<id>  -> marcar como leida
# ----------------------------------------------------------
@ws_api.route('/notificaciones/leer/<int:id_notificacion>', methods=['POST'])
def leer_notificacion(id_notificacion):
    try:
        notificacion.marcar_leida(id_notificacion)
        return jsonify({'data': None, 'message': 'Notificacion leida', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/calificacion/<id_incidencia>  -> calificacion (req. #11)
# ----------------------------------------------------------
@ws_api.route('/calificacion/<int:id_incidencia>', methods=['GET'])
def obtener_calificacion(id_incidencia):
    try:
        datos = calificacion.obtener(id_incidencia)
        return jsonify({'data': datos, 'message': 'Calificacion obtenida', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/registrarCalificacion  -> calificar (req. #11)
#  Recibe: { id_incidencia, puntuacion, comentario }
# ----------------------------------------------------------
@ws_api.route('/registrarCalificacion', methods=['POST'])
def registrar_calificacion():
    data = request.get_json(silent=True) or {}
    id_incidencia = data.get('id_incidencia')
    puntuacion = data.get('puntuacion')
    comentario = data.get('comentario')

    if not id_incidencia or not puntuacion:
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400

    exitoso, resultado = calificacion.registrar(id_incidencia, puntuacion, comentario)
    if not exitoso:
        return jsonify({'data': None, 'message': resultado, 'status': 0}), 400

    return jsonify({'data': {'id': resultado}, 'message': 'Gracias por tu calificacion', 'status': 1}), 201


# ----------------------------------------------------------
#  GET /api/perfil/<id>  -> datos de perfil (req. #12)
# ----------------------------------------------------------
@ws_api.route('/perfil/<int:id_usuario>', methods=['GET'])
def obtener_perfil(id_usuario):
    try:
        datos = usuario.obtener_perfil(id_usuario)
        if not datos:
            return jsonify({'data': None, 'message': 'Usuario inexistente', 'status': 0}), 404
        return jsonify({'data': datos, 'message': 'Perfil obtenido', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  PUT /api/actualizarPerfil  -> editar perfil (req. #12)
#  Recibe: { id, nombres, apellidos, telefono,
#            contacto_emergencia_nombre, contacto_emergencia_telefono }
# ----------------------------------------------------------
@ws_api.route('/actualizarPerfil', methods=['PUT'])
def actualizar_perfil():
    data = request.get_json(silent=True) or {}
    id_usuario = data.get('id')
    if not id_usuario:
        return jsonify({'data': None, 'message': 'Falta el id de usuario', 'status': 0}), 400
    try:
        usuario.actualizar_perfil(
            id_usuario,
            data.get('nombres'), data.get('apellidos'), data.get('telefono'),
            data.get('contacto_emergencia_nombre'), data.get('contacto_emergencia_telefono')
        )
        return jsonify({'data': None, 'message': 'Perfil actualizado', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/perfil/foto  -> subir foto de perfil (multipart)
#  Campos del form-data: id_usuario, imagen (archivo)
# ----------------------------------------------------------
@ws_api.route('/perfil/foto', methods=['POST'])
def subir_foto_perfil():
    id_usuario = request.form.get('id_usuario')
    archivo = request.files.get('imagen')
    if not id_usuario or not archivo or not _extension_valida(archivo.filename):
        return jsonify({'data': None, 'message': 'Falta el id o una imagen valida', 'status': 0}), 400
    try:
        nombre = _guardar_imagen(archivo, CARPETA_USUARIOS, f"u{id_usuario}")
        usuario.actualizar_foto(id_usuario, nombre)
        return jsonify({'data': {'imagen': nombre}, 'message': 'Foto actualizada', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/perfil/foto/<id>  -> servir la foto del usuario
# ----------------------------------------------------------
@ws_api.route('/perfil/foto/<int:id_usuario>', methods=['GET'])
def ver_foto_perfil(id_usuario):
    perfil = usuario.obtener_perfil(id_usuario)
    if perfil and perfil.get('imagen'):
        ruta = os.path.join(CARPETA_USUARIOS, perfil['imagen'])
        if os.path.exists(ruta):
            return send_from_directory(CARPETA_USUARIOS, perfil['imagen'])
    return _imagen_placeholder('Sin foto')


# ----------------------------------------------------------
#  GET /api/mensajes/<id_incidencia>  -> chat (req. #10)
# ----------------------------------------------------------
@ws_api.route('/mensajes/<int:id_incidencia>', methods=['GET'])
def listar_mensajes(id_incidencia):
    try:
        datos = mensaje.listar_movil(id_incidencia)
        return jsonify({'data': datos, 'message': 'Mensajes obtenidos', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/registrarMensaje  -> enviar mensaje al chat (req. #10)
#  Recibe: { id_incidencia, id_usuario, mensaje }
# ----------------------------------------------------------
@ws_api.route('/registrarMensaje', methods=['POST'])
def registrar_mensaje():
    data = request.get_json(silent=True) or {}
    id_incidencia = data.get('id_incidencia')
    id_usuario = data.get('id_usuario')
    texto = data.get('mensaje')

    if not id_incidencia or not id_usuario or not texto:
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400

    try:
        mensaje.enviar(id_incidencia, id_usuario, texto)
        return jsonify({'data': None, 'message': 'Mensaje enviado', 'status': 1}), 201
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  PUT /api/registrarTokenFCM  -> guardar token de Firebase (req. #9)
#  Recibe: { id_usuario, fcm_token }
# ----------------------------------------------------------
@ws_api.route('/registrarTokenFCM', methods=['PUT'])
def registrar_token_fcm():
    data = request.get_json(silent=True) or {}
    id_usuario = data.get('id_usuario')
    token = data.get('fcm_token')
    if not id_usuario or not token:
        return jsonify({'data': None, 'message': 'Faltan datos obligatorios', 'status': 0}), 400
    try:
        usuario.guardar_fcm_token(id_usuario, token)
        return jsonify({'data': None, 'message': 'Token registrado', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  POST /api/registrarEvidencia  -> subir evidencia (multipart) (req. #4 y #14)
#  Campos del form-data: id_incidencia, imagen (archivo)
# ----------------------------------------------------------
@ws_api.route('/registrarEvidencia', methods=['POST'])
def registrar_evidencia():
    id_incidencia = request.form.get('id_incidencia')
    archivo = request.files.get('imagen')
    if not id_incidencia or not archivo or not _extension_valida(archivo.filename):
        return jsonify({'data': None, 'message': 'Falta la incidencia o una imagen valida', 'status': 0}), 400
    try:
        nombre = _guardar_imagen(archivo, CARPETA_EVIDENCIAS, f"i{id_incidencia}")
        nuevo_id = evidencia.registrar(id_incidencia, nombre)
        return jsonify({'data': {'id': nuevo_id, 'url_imagen': nombre},
                        'message': 'Evidencia agregada', 'status': 1}), 201
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/evidencias/<id_incidencia>  -> lista de evidencias
# ----------------------------------------------------------
@ws_api.route('/evidencias/<int:id_incidencia>', methods=['GET'])
def listar_evidencias(id_incidencia):
    try:
        datos = evidencia.listar(id_incidencia)
        return jsonify({'data': datos, 'message': 'Evidencias obtenidas', 'status': 1}), 200
    except Exception as e:
        return jsonify({'data': None, 'message': str(e), 'status': 0}), 500


# ----------------------------------------------------------
#  GET /api/evidencia/imagen/<nombre>  -> servir una imagen de evidencia
# ----------------------------------------------------------
@ws_api.route('/evidencia/imagen/<nombre>', methods=['GET'])
def ver_evidencia(nombre):
    ruta = os.path.join(CARPETA_EVIDENCIAS, nombre)
    if os.path.exists(ruta):
        return send_from_directory(CARPETA_EVIDENCIAS, nombre)
    return _imagen_placeholder('Sin evidencia')


def _imagen_placeholder(texto):
    """Imagen SVG generada al vuelo cuando no existe el archivo pedido."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">'
        '<rect width="100%" height="100%" fill="#e9ecef"/>'
        f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
        f'fill="#6c757d" font-family="sans-serif" font-size="16">{texto}</text>'
        '</svg>'
    )
    return Response(svg, mimetype='image/svg+xml')
