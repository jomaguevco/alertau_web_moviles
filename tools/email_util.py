# ============================================================
#  tools/email_util.py  -  Envio de correo (HTTP Brevo / SMTP)
# ------------------------------------------------------------
#  Se usa para enviar el codigo de recuperacion de contrasena
#  (req. movil #3).
#
#  IMPORTANTE - por que hay DOS formas de enviar:
#   - En la NUBE (Railway) el puerto SMTP saliente esta BLOQUEADO,
#     asi que el envio por SMTP falla con "Network is unreachable".
#   - Por eso, si esta configurada la variable BREVO_API_KEY, se
#     envia por HTTP (HTTPS puerto 443), que Railway si permite.
#   - Si NO hay BREVO_API_KEY, se usa SMTP (sirve en local / XAMPP).
#
#  Si nada esta configurado, no se envia pero la app NO se cae
#  (devuelve False) y se imprime el motivo EXACTO en el log.
# ============================================================
import base64
import json
import smtplib
import ssl
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from config import Config


def enviar_correo(destinatario, asunto, cuerpo):
    """
    Envia un correo de texto plano. Devuelve True si se envio, False si no.

    Elige el metodo segun la configuracion (los HTTP funcionan en Railway):
      1) Si hay MAILJET_API_KEY + MAILJET_SECRET_KEY -> envia por HTTP (Mailjet).
      2) Si hay BREVO_API_KEY                        -> envia por HTTP (Brevo).
      3) Si no, pero hay SMTP                         -> envia por SMTP (local).
      4) Si no hay nada                               -> no envia (devuelve False).
    """
    # 1) Mailjet (HTTP) - funciona tanto en la nube (Railway) como en local.
    if Config.MAILJET_API_KEY and Config.MAILJET_SECRET_KEY:
        return _enviar_por_mailjet(destinatario, asunto, cuerpo)

    # 2) Brevo (HTTP) - alternativa que tambien funciona en la nube.
    if Config.BREVO_API_KEY:
        return _enviar_por_brevo(destinatario, asunto, cuerpo)

    # 3) Si no hay servicio HTTP, intentar por SMTP (tipico en local / XAMPP).
    if Config.SMTP_HOST and Config.SMTP_USER and Config.SMTP_PASSWORD:
        return _enviar_por_smtp(destinatario, asunto, cuerpo)

    # 4) Nada configurado.
    print("[email_util] No hay forma de enviar: configura MAILJET_API_KEY+MAILJET_SECRET_KEY "
          "o BREVO_API_KEY (nube), o SMTP_HOST/SMTP_USER/SMTP_PASSWORD (local).")
    return False


def _enviar_por_mailjet(destinatario, asunto, cuerpo):
    """
    Envia el correo usando la API HTTP de Mailjet (https://api.mailjet.com).
    Funciona en Railway porque usa HTTPS (puerto 443), no el puerto SMTP.
    Autenticacion: HTTP Basic con la API Key (publica) y la Secret Key (privada).
    """
    if not Config.MAILJET_SENDER:
        print("[email_util] Falta MAILJET_SENDER (o SMTP_FROM) con el correo remitente verificado en Mailjet.")
        return False

    url = "https://api.mailjet.com/v3.1/send"
    payload = {
        "Messages": [
            {
                "From": {"Email": Config.MAILJET_SENDER, "Name": Config.MAILJET_SENDER_NAME},
                "To": [{"Email": destinatario}],
                "Subject": asunto,
                "TextPart": cuerpo,
            }
        ]
    }
    datos = json.dumps(payload).encode("utf-8")

    # Mailjet usa autenticacion basica: base64("apikey:secretkey").
    credenciales = f"{Config.MAILJET_API_KEY}:{Config.MAILJET_SECRET_KEY}"
    auth = base64.b64encode(credenciales.encode("utf-8")).decode("ascii")

    peticion = urllib.request.Request(url, data=datos, method="POST")
    peticion.add_header("Authorization", f"Basic {auth}")
    peticion.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(peticion, timeout=15) as respuesta:
            if respuesta.status in (200, 201):
                print(f"[email_util] Correo enviado a {destinatario} por Mailjet (HTTP).")
                return True
            print(f"[email_util] Mailjet respondio codigo inesperado {respuesta.status} "
                  f"al enviar a {destinatario}.")
            return False
    except urllib.error.HTTPError as e:
        # Leemos el cuerpo del error para saber EXACTAMENTE que paso
        # (p. ej. remitente no verificado o claves invalidas).
        detalle = e.read().decode("utf-8", "replace") if e.fp else ""
        print(f"[email_util] Mailjet rechazo el envio a {destinatario}: "
              f"HTTP {e.code} - {detalle}")
        return False
    except Exception as e:
        print(f"[email_util] No se pudo enviar por Mailjet a {destinatario}: "
              f"{type(e).__name__}: {e}")
        return False


def _enviar_por_brevo(destinatario, asunto, cuerpo):
    """
    Envia el correo usando la API HTTP de Brevo (https://api.brevo.com).
    Funciona en Railway porque usa HTTPS (puerto 443), no el puerto SMTP.
    """
    if not Config.BREVO_SENDER:
        print("[email_util] Falta BREVO_SENDER (o SMTP_FROM) con el correo remitente verificado en Brevo.")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"email": Config.BREVO_SENDER, "name": Config.BREVO_SENDER_NAME},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "textContent": cuerpo,
    }
    datos = json.dumps(payload).encode("utf-8")
    peticion = urllib.request.Request(url, data=datos, method="POST")
    peticion.add_header("api-key", Config.BREVO_API_KEY)
    peticion.add_header("Content-Type", "application/json")
    peticion.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(peticion, timeout=15) as respuesta:
            # Brevo responde 201 (Created) cuando acepta el correo.
            if respuesta.status in (200, 201):
                print(f"[email_util] Correo enviado a {destinatario} por Brevo (HTTP).")
                return True
            print(f"[email_util] Brevo respondio codigo inesperado {respuesta.status} "
                  f"al enviar a {destinatario}.")
            return False
    except urllib.error.HTTPError as e:
        # Error con cuerpo: lo leemos para saber EXACTAMENTE que paso
        # (p. ej. remitente no verificado o API key invalida).
        detalle = e.read().decode("utf-8", "replace") if e.fp else ""
        print(f"[email_util] Brevo rechazo el envio a {destinatario}: "
              f"HTTP {e.code} - {detalle}")
        return False
    except Exception as e:
        print(f"[email_util] No se pudo enviar por Brevo a {destinatario}: "
              f"{type(e).__name__}: {e}")
        return False


def _enviar_por_smtp(destinatario, asunto, cuerpo):
    """
    Envia el correo por SMTP (puerto 587 STARTTLS o 465 SSL).
    Sirve en local; en Railway suele fallar porque el puerto SMTP esta bloqueado.
    """
    try:
        mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
        mensaje['Subject'] = asunto
        mensaje['From'] = Config.SMTP_FROM
        mensaje['To'] = destinatario

        if int(Config.SMTP_PORT) == 465:
            # Conexion cifrada desde el inicio (SSL directo).
            contexto = ssl.create_default_context()
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT,
                                  context=contexto, timeout=15) as servidor:
                servidor.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                servidor.sendmail(Config.SMTP_FROM, [destinatario], mensaje.as_string())
        else:
            # Conexion normal que se actualiza a TLS (puerto 587 tipico de Gmail).
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as servidor:
                servidor.starttls(context=ssl.create_default_context())
                servidor.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                servidor.sendmail(Config.SMTP_FROM, [destinatario], mensaje.as_string())

        print(f"[email_util] Correo enviado a {destinatario} por SMTP.")
        return True
    except Exception as e:
        # No interrumpimos el flujo si el correo falla; solo lo registramos
        # con el detalle para saber EXACTAMENTE por que no se envio.
        print(f"[email_util] No se pudo enviar el correo a {destinatario} por SMTP: "
              f"{type(e).__name__}: {e}")
        return False
