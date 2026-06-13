# ============================================================
#  tools/fcm.py  -  Notificaciones push con Firebase (req. #9)
# ------------------------------------------------------------
#  Envia notificaciones push a la app movil usando Firebase Cloud
#  Messaging (FCM). La inicializacion es PEREZOSA y PROTEGIDA: si
#  firebase-admin no esta instalado o no hay credenciales, las
#  funciones simplemente no envian nada (devuelven False) y la app
#  NO se cae. Asi el codigo ya esta listo y se activa cuando se
#  configuren las credenciales (ver Fase 3 / README).
#
#  Credenciales (variable de entorno, una de las dos):
#    - FIREBASE_CREDENTIALS         -> el JSON de la cuenta de servicio (texto)
#    - GOOGLE_APPLICATION_CREDENTIALS -> ruta a ese archivo .json
# ============================================================
import os
import json

# Estado interno de inicializacion (se intenta una sola vez).
_app = None
_intentado = False
_messaging = None


def _inicializar():
    """Inicializa Firebase Admin una sola vez. Devuelve True si quedo listo."""
    global _app, _intentado, _messaging
    if _intentado:
        return _app is not None
    _intentado = True

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        _messaging = messaging

        cred = None
        cred_json = os.environ.get('FIREBASE_CREDENTIALS')
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Sin credenciales: no se puede enviar push.
            return False

        _app = firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"[fcm] No se pudo inicializar Firebase: {e}")
        return False


def enviar_push(token, titulo, cuerpo):
    """
    Envia una notificacion push a un dispositivo (por su token FCM).
    Devuelve True si se envio, False si no hay token o Firebase no esta listo.
    """
    if not token:
        return False
    if not _inicializar():
        return False
    try:
        mensaje = _messaging.Message(
            notification=_messaging.Notification(title=titulo, body=cuerpo),
            token=token,
        )
        _messaging.send(mensaje)
        return True
    except Exception as e:
        print(f"[fcm] No se pudo enviar el push: {e}")
        return False
