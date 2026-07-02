# ============================================================
#  routes/ubicaciones.py  -  Generacion de codigos QR de ambientes
# ------------------------------------------------------------
#  Cada aula/laboratorio/taller tiene un codigo (ubicacion.codigo_qr)
#  que la app movil reconoce al escanear (req. movil #4). Esta pagina
#  dibuja esos QR listos para imprimir y pegar en cada ambiente.
# ============================================================
from flask import Blueprint, render_template
from models.catalogo import Catalogo
from tools.auth_required import login_requerido

ws_ubicaciones = Blueprint('ws_ubicaciones', __name__)

catalogo = Catalogo()


# ----------------------------------------------------------
#  Codigos QR de los ambientes (para imprimir)
# ----------------------------------------------------------
@ws_ubicaciones.route('/ubicaciones/qr')
@login_requerido
def qr():
    # Solo las ubicaciones con codigo_qr (aulas, labs, talleres). Las zonas de
    # atencion y puntos de apoyo no necesitan QR, por eso se filtran.
    ubicaciones = [u for u in catalogo.ubicaciones() if u.get('codigo_qr')]
    return render_template('ubicaciones/qr.html', ubicaciones=ubicaciones)
