# ============================================================
#  tools/security.py  -  Utilidades de seguridad (contrasenas)
# ------------------------------------------------------------
#  Las contrasenas NUNCA se guardan en texto plano. Se guarda
#  un "hash" calculado con argon2 (algoritmo recomendado hoy).
#   - hash_password()    -> al registrar/cambiar la clave.
#   - verificar_password()-> al iniciar sesion.
# ============================================================
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Un unico objeto PasswordHasher reutilizable en toda la app.
ph = PasswordHasher()


def hash_password(password_plain):
    """Devuelve el hash argon2 de una contrasena en texto plano."""
    return ph.hash(password_plain)


def verificar_password(hash_guardado, password_plain):
    """
    Compara la contrasena escrita por el usuario con el hash de la BD.
    Devuelve True si coinciden, False si no.
    """
    try:
        ph.verify(hash_guardado, password_plain)
        return True
    except VerifyMismatchError:
        return False
