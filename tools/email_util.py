# ============================================================
#  tools/email_util.py  -  Envio de correo por SMTP
# ------------------------------------------------------------
#  Se usa para enviar el codigo de recuperacion de contrasena
#  (req. movil #3). La configuracion sale de variables de entorno
#  (config.SMTP_*). Si no estan configuradas, no se envia nada
#  pero la app NO se cae (devuelve False).
# ============================================================
import smtplib
from email.mime.text import MIMEText
from config import Config


def enviar_correo(destinatario, asunto, cuerpo):
    """
    Envia un correo de texto plano. Devuelve True si se envio,
    False si SMTP no esta configurado o si ocurrio un error.
    """
    # Si no hay servidor SMTP configurado, no intentamos enviar.
    if not Config.SMTP_HOST or not Config.SMTP_USER:
        return False

    try:
        mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
        mensaje['Subject'] = asunto
        mensaje['From'] = Config.SMTP_FROM
        mensaje['To'] = destinatario

        # Conexion con TLS (puerto 587 tipico de Gmail).
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            servidor.sendmail(Config.SMTP_FROM, [destinatario], mensaje.as_string())
        return True
    except Exception as e:
        # No interrumpimos el flujo si el correo falla; solo lo registramos.
        print(f"[email_util] No se pudo enviar el correo: {e}")
        return False
