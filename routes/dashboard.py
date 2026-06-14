# ============================================================
#  routes/dashboard.py  -  Panel resumen (req. web #10)
# ------------------------------------------------------------
#  Muestra los indicadores clave: total de incidencias, casos
#  criticos, % de casos cerrados, e incidencias por categoria,
#  urgencia y estado.
# ============================================================
from flask import Blueprint, render_template
from models.reporte import Reporte
from tools.auth_required import login_requerido

ws_dashboard = Blueprint('ws_dashboard', __name__)

reporte = Reporte()


@ws_dashboard.route('/dashboard')
@login_requerido
def dashboard():
    # Indicadores para las tarjetas y los graficos del panel.
    resumen = reporte.resumen()
    por_categoria = reporte.por_categoria()
    por_urgencia = reporte.por_urgencia()
    por_estado = reporte.por_estado()
    tiempo_promedio = reporte.tiempo_promedio_general()   # req. #10

    return render_template(
        'dashboard.html',
        resumen=resumen,
        por_categoria=por_categoria,
        por_urgencia=por_urgencia,
        por_estado=por_estado,
        tiempo_promedio=tiempo_promedio,
    )
