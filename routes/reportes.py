# ============================================================
#  routes/reportes.py  -  Reportes del panel web
# ------------------------------------------------------------
#  Cubre los requerimientos web:
#   #8 Reporte geografico de incidencias (mapa)
#   #9 Reportes administrativos (por tipo/rango, urgencia,
#      tiempo promedio de atencion, resueltas con calificacion)
# ============================================================
from flask import Blueprint, render_template, request
from models.reporte import Reporte
from tools.auth_required import login_requerido

ws_reportes = Blueprint('ws_reportes', __name__)

reporte = Reporte()


# ----------------------------------------------------------
#  #8  Reporte geografico (mapa de incidencias)
# ----------------------------------------------------------
@ws_reportes.route('/reporte-mapa')
@login_requerido
def reporte_mapa():
    # Convertir a tipos simples (float) para poder enviarlo como JSON al mapa.
    incidencias = []
    for fila in reporte.incidencias_geo():
        incidencias.append({
            'id': fila['id'],
            'descripcion': fila['descripcion'],
            'latitud': float(fila['latitud']),
            'longitud': float(fila['longitud']),
            'estado': fila['estado'],
            'categoria': fila['categoria'],
            'urgencia': fila['urgencia'],
        })
    return render_template('reportes/mapa.html', incidencias=incidencias)


# ----------------------------------------------------------
#  #9  Reportes administrativos
# ----------------------------------------------------------
@ws_reportes.route('/reportes')
@login_requerido
def reportes():
    # Filtro opcional por rango de fechas (para "incidencias por tipo en rango").
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    return render_template(
        'reportes/reportes.html',
        por_categoria=reporte.por_categoria_rango(fecha_desde, fecha_hasta),
        por_urgencia=reporte.por_urgencia(),
        tiempo_promedio=reporte.tiempo_promedio_por_tipo(),
        resueltas=reporte.resueltas_con_calificacion(),
        filtros={'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
    )
