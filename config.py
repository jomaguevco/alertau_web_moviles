import os

from dotenv import load_dotenv

# Carga variables desde un archivo .env si existe (solo para desarrollo local).
# En Railway las variables de entorno se inyectan automaticamente, asi que
# esta linea no estorba en produccion.
load_dotenv()


class Config:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "incidencias_campus")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
