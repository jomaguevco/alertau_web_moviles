# ============================================================
#  tools/probar_correo.py  -  Prueba rapida del envio de correo
# ------------------------------------------------------------
#  Sirve para comprobar que el SMTP del .env esta bien
#  configurado, SIN levantar toda la app ni la app movil.
#
#  Uso (desde la carpeta AlertaU-web):
#     venv\Scripts\python.exe -m tools.probar_correo  tu_destino@gmail.com
#
#  Si todo esta bien, llega un correo de prueba al destino.
#  Si falla, se imprime el error EXACTO (clave mal puesta, etc.).
# ============================================================
import sys
from config import Config
from tools.email_util import enviar_correo


def main():
    # Destino: el correo que escribas como argumento, o SMTP_USER por defecto.
    destino = sys.argv[1] if len(sys.argv) > 1 else Config.SMTP_USER

    print("=== Configuracion SMTP leida del .env ===")
    print(f"  SMTP_HOST = {Config.SMTP_HOST or '(vacio)'}")
    print(f"  SMTP_PORT = {Config.SMTP_PORT}")
    print(f"  SMTP_USER = {Config.SMTP_USER or '(vacio)'}")
    print(f"  SMTP_PASSWORD = {'(configurada)' if Config.SMTP_PASSWORD else '(vacio)'}")
    print(f"  SMTP_FROM = {Config.SMTP_FROM or '(vacio)'}")
    print(f"  Destino   = {destino}")
    print("==========================================")

    if not destino:
        print("ERROR: no hay destino. Pasa un correo: python -m tools.probar_correo correo@dominio.com")
        return

    ok = enviar_correo(
        destino,
        "Prueba de correo - AlertaU",
        "Si lees esto, el envio de codigos de AlertaU funciona correctamente.",
    )
    print("\nRESULTADO:", "CORREO ENVIADO OK" if ok else "NO SE PUDO ENVIAR (revisa el error de arriba)")


if __name__ == "__main__":
    main()
