# ============================================================
#  tools/email_util.py  -  Envio de correo por SMTP
# ------------------------------------------------------------
#  Se usa para enviar el codigo de recuperacion de contrasena
#  (req. movil #3). La configuracion sale de variables de entorno
#  (config.SMTP_*). Si no estan configuradas, no se envia nada
#  pero la app NO se cae (devuelve False).
# ============================================================
import smtplib
import ssl
from email.mime.text import MIMEText
from config import Config


def enviar_correo(destinatario, asunto, cuerpo):
    """
    Envia un correo de texto plano. Devuelve True si se envio,
    False si SMTP no esta configurado o si ocurrio un error.

    Soporta los dos modos tipicos de Gmail y otros proveedores:
      - Puerto 587 (STARTTLS)  -> el mas comun
      - Puerto 465 (SSL/TLS)   -> si SMTP_PORT=465
    Si algo falla, se imprime el error EXACTO en el log para poder
    diagnosticar (p. ej. "Username and Password not accepted" cuando
    la contrasena de aplicacion de Gmail caduco o se revoco).
    """
    # Si no hay servidor SMTP configurado, no intentamos enviar.
    if not Config.SMTP_HOST or not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        print("[email_util] SMTP no configurado (faltan SMTP_HOST / SMTP_USER / SMTP_PASSWORD).")
        return False

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

        print(f"[email_util] Correo enviado a {destinatario}.")
        return True
    except Exception as e:
        # No interrumpimos el flujo si el correo falla; solo lo registramos
        # con el detalle para saber EXACTAMENTE por que no se envio.
        print(f"[email_util] No se pudo enviar el correo a {destinatario}: "
              f"{type(e).__name__}: {e}")
        return False
