# ============================================================
#  tools/notificar.py  -  Notificar a un usuario (req. #9)
# ------------------------------------------------------------
#  Junta las dos partes de una notificacion:
#    1) guardar el aviso en la tabla 'notificacion' (historial in-app)
#    2) enviar el push por Firebase si el usuario tiene token (tools/fcm.py)
#  Se usa cuando: se recibe un caso, cambia de estado, se deriva o se cierra.
# ============================================================
from conexionBD import Conexion
from models.notificacion import Notificacion
from tools.fcm import enviar_push

_notificacion = Notificacion()


def notificar_usuario(id_usuario, mensaje, titulo='AlertaU'):
    """Guarda la notificacion en la BD y, si se puede, envia el push al dispositivo."""
    if not id_usuario:
        return

    # 1) Guardar el aviso en el historial (in-app).
    try:
        _notificacion.crear(id_usuario, mensaje)
    except Exception as e:
        print(f"[notificar] No se pudo guardar la notificacion: {e}")

    # 2) Buscar el token FCM del usuario y enviar el push (si tiene token).
    token = None
    try:
        con = Conexion().open
        cur = con.cursor()
        cur.execute("SELECT fcm_token FROM usuario WHERE id = %s", [id_usuario])
        fila = cur.fetchone()
        token = fila['fcm_token'] if fila else None
        cur.close()
        con.close()
    except Exception as e:
        print(f"[notificar] No se pudo leer el token: {e}")

    enviar_push(token, titulo, mensaje)


def notificar_personal(mensaje, titulo='AlertaU', roles=(3, 4)):
    """Notifica (in-app + push) a TODO el personal de los roles indicados.
    Por defecto Administrativo (3) y Personal autorizado (4). Se usa para
    avisar a seguridad cuando entra una alerta rapida (boton de panico)."""
    try:
        con = Conexion().open
        cur = con.cursor()
        marcadores = ','.join(['%s'] * len(roles))
        cur.execute(
            f"SELECT id, fcm_token FROM usuario "
            f"WHERE id_tipo_usuario IN ({marcadores}) AND estado = 1",
            list(roles)
        )
        filas = cur.fetchall()
        cur.close()
        con.close()
    except Exception as e:
        print(f"[notificar] No se pudo leer el personal: {e}")
        return

    for f in filas:
        try:
            _notificacion.crear(f['id'], mensaje)
        except Exception as e:
            print(f"[notificar] No se pudo guardar aviso al personal {f['id']}: {e}")
        enviar_push(f.get('fcm_token'), titulo, mensaje)
