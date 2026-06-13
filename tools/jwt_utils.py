# ============================================================
#  tools/jwt_utils.py  -  Generacion y verificacion de JWT
# ------------------------------------------------------------
#  La app movil inicia sesion y recibe un "access_token" (JWT).
#  En cada peticion posterior lo envia en la cabecera:
#       Authorization: Bearer <token>
#  Aqui se crea y se valida ese token (algoritmo HS256).
# ============================================================
import jwt
from datetime import datetime, timedelta
from config import Config


def generar_token(payload, exp_seconds=60 * 60):
    """
    Crea un token JWT firmado con la clave secreta.
    'payload' suele ser {'usuario_id': X}. 'exp_seconds' = tiempo de vida.
    """
    payload = dict(payload)  # copia para no modificar el original
    payload['exp'] = datetime.utcnow() + timedelta(seconds=exp_seconds)
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    return token


def verificar_token(token):
    """
    Valida un token. Devuelve el payload si es valido,
    o None si esta expirado o es invalido.
    """
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
