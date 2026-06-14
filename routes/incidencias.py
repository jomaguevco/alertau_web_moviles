# ============================================================
#  routes/incidencias.py  -  Gestion de incidencias
# ------------------------------------------------------------
#  Cubre los requerimientos web:
#   #2 Gestion de incidencias (lista con filtros)
#   #3 Clasificacion y derivacion de casos
#   #4 Cambio de estados con trazabilidad
#   #5 Visualizacion de evidencias
#   #7 Respuesta y seguimiento (chat)
# ============================================================
import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, send_from_directory, Response)
from config import Config
from models.incidencia import Incidencia
from models.catalogo import Catalogo
from models.mensaje import Mensaje
from models.usuario import Usuario
from tools.auth_required import login_requerido
from tools.notificar import notificar_usuario

ws_incidencias = Blueprint('ws_incidencias', __name__)

incidencia = Incidencia()
catalogo = Catalogo()
mensaje = Mensaje()
usuario = Usuario()

# Carpeta donde se guardan/leen las imagenes de evidencia (misma que usa la API
# movil, configurable por UPLOAD_DIR para el volumen persistente de Railway).
CARPETA_EVIDENCIAS = os.path.join(Config.UPLOAD_DIR, 'evidencias')


# ----------------------------------------------------------
#  #2  Lista de incidencias con filtros
# ----------------------------------------------------------
@ws_incidencias.route('/incidencias')
@login_requerido
def lista():
    # Leer los filtros desde la URL (?id_estado=...&id_categoria=...).
    # request.args.get devuelve None si el filtro no fue enviado.
    filtros = {
        'id_estado': request.args.get('id_estado'),
        'id_categoria': request.args.get('id_categoria'),
        'id_urgencia': request.args.get('id_urgencia'),
        'id_area': request.args.get('id_area'),
        'usuario': request.args.get('usuario'),
        'fecha_desde': request.args.get('fecha_desde'),
        'fecha_hasta': request.args.get('fecha_hasta'),
    }

    incidencias = incidencia.listar(filtros)

    # Catalogos para llenar los <select> de los filtros.
    return render_template(
        'incidencias/lista.html',
        incidencias=incidencias,
        estados=catalogo.estados(),
        categorias=catalogo.categorias(),
        urgencias=catalogo.urgencias(),
        areas=catalogo.areas(),
        filtros=filtros,
    )


# ----------------------------------------------------------
#  #5  Detalle de una incidencia (evidencias, linea de tiempo, chat)
# ----------------------------------------------------------
@ws_incidencias.route('/incidencias/<int:id_incidencia>')
@login_requerido
def detalle(id_incidencia):
    datos = incidencia.obtener(id_incidencia)
    if not datos:
        flash('La incidencia no existe.', 'danger')
        return redirect(url_for('ws_incidencias.lista'))

    return render_template(
        'incidencias/detalle.html',
        inc=datos,
        evidencias=incidencia.listar_evidencias(id_incidencia),
        linea_tiempo=incidencia.linea_tiempo(id_incidencia),
        derivaciones=incidencia.derivaciones(id_incidencia),
        mensajes=mensaje.listar(id_incidencia),
        estados=catalogo.estados(),
        areas=catalogo.areas(),
    )


# ----------------------------------------------------------
#  #4  Cambiar el estado (con trazabilidad)
# ----------------------------------------------------------
@ws_incidencias.route('/incidencias/<int:id_incidencia>/estado', methods=['POST'])
@login_requerido
def cambiar_estado(id_incidencia):
    id_estado = request.form.get('id_estado')
    comentario = request.form.get('comentario', '').strip() or None

    if not id_estado:
        flash('Debes seleccionar un estado.', 'danger')
        return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))

    # session['usuario_id'] = quien hace el cambio (trazabilidad).
    incidencia.cambiar_estado(id_incidencia, id_estado, session['usuario_id'], comentario)

    # Notificar al usuario que reporto la incidencia (req. #9).
    reportante = usuario.fcm_token_de_incidencia(id_incidencia)
    if reportante:
        notificar_usuario(reportante['id_usuario'],
                          f'El estado de tu incidencia #{id_incidencia} fue actualizado.')

    flash('Estado actualizado correctamente.', 'success')
    return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))


# ----------------------------------------------------------
#  #3  Derivar a un area responsable
# ----------------------------------------------------------
@ws_incidencias.route('/incidencias/<int:id_incidencia>/derivar', methods=['POST'])
@login_requerido
def derivar(id_incidencia):
    id_area = request.form.get('id_area')
    comentario = request.form.get('comentario', '').strip() or None

    if not id_area:
        flash('Debes seleccionar un area.', 'danger')
        return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))

    incidencia.derivar(id_incidencia, id_area, session['usuario_id'], comentario)

    # Notificar al usuario que reporto la incidencia (req. #9).
    reportante = usuario.fcm_token_de_incidencia(id_incidencia)
    if reportante:
        notificar_usuario(reportante['id_usuario'],
                          f'Tu incidencia #{id_incidencia} fue derivada a un area responsable.')

    flash('Incidencia derivada correctamente.', 'success')
    return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))


# ----------------------------------------------------------
#  #7  Enviar un mensaje en el chat de la incidencia
# ----------------------------------------------------------
@ws_incidencias.route('/incidencias/<int:id_incidencia>/mensaje', methods=['POST'])
@login_requerido
def enviar_mensaje(id_incidencia):
    texto = request.form.get('mensaje', '').strip()
    if not texto:
        flash('El mensaje no puede estar vacio.', 'danger')
        return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))

    mensaje.enviar(id_incidencia, session['usuario_id'], texto)
    flash('Mensaje enviado.', 'success')
    return redirect(url_for('ws_incidencias.detalle', id_incidencia=id_incidencia))


# ----------------------------------------------------------
#  Servir las imagenes de evidencia guardadas en /uploads
# ----------------------------------------------------------
@ws_incidencias.route('/evidencia/<nombre_imagen>')
@login_requerido
def ver_evidencia(nombre_imagen):
    # Si la imagen existe se envia; si no, se devuelve una imagen SVG
    # "Sin evidencia" generada al vuelo (asi no dependemos de un archivo binario).
    ruta = os.path.join(CARPETA_EVIDENCIAS, nombre_imagen)
    if os.path.exists(ruta):
        return send_from_directory(CARPETA_EVIDENCIAS, nombre_imagen)

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">'
        '<rect width="100%" height="100%" fill="#e9ecef"/>'
        '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
        'fill="#6c757d" font-family="sans-serif" font-size="16">Sin evidencia</text>'
        '</svg>'
    )
    return Response(svg, mimetype='image/svg+xml')
