# AlertaU - Panel Web (Flask)

Aplicacion **web responsable** para el personal autorizado del campus, parte del
proyecto *App de Gestion de Incidencias y Atencion de Emergencias en Campus
Universitario*. Cubre la **seccion 4** del documento del proyecto: gestion de
incidencias, derivacion, cambio de estados con trazabilidad, evidencias, chat,
gestion de usuarios y panel resumen.

> La aplicacion **movil** (estudiantes/docentes) y la **API REST con JWT** que
> ella consumira se construiran en una etapa posterior, reutilizando esta misma
> base de datos.

## Tecnologias

- **Backend:** Flask (Python) con plantillas Jinja2 (paginas renderizadas en el servidor).
- **Base de datos:** MySQL (`incidencias_campus`), driver `mysqlclient`.
- **Frontend:** Bootstrap 5 + HTML5 + JavaScript (incluido por CDN).
- **Seguridad:** contrasenas con `argon2`, login por **sesion** de Flask.

## Estructura

```
.
├── app.py                  # Punto de entrada (registra los blueprints)
├── config.py               # Configuracion por variables de entorno
├── conexionBD.py           # Conexion a MySQL
├── incidencias_campus.sql  # Esquema + datos semilla (importar en phpMyAdmin)
├── requirements.txt        # Dependencias
├── Procfile                # Arranque en la nube (gunicorn)
├── .env.example            # Plantilla de variables de entorno
├── models/                 # Acceso a datos (consultas SQL comentadas)
├── routes/                 # Rutas / paginas (blueprints)
├── tools/                  # Seguridad (argon2) y control de sesion
├── templates/              # Vistas HTML (Bootstrap)
├── static/                 # css y js
└── uploads/                # Imagenes (evidencias y fotos de usuario)
```

## Instalacion y ejecucion local (Windows + XAMPP)

1. **Iniciar MySQL** desde el panel de XAMPP.
2. **Importar la base de datos**: en phpMyAdmin (`http://localhost/phpmyadmin`)
   importar el archivo `incidencias_campus.sql`. Crea la BD `incidencias_campus`
   con catalogos, usuarios de prueba y datos de ejemplo.
3. **Instalar dependencias y ejecutar**:

   ```bash
   python -m venv venv
   venv\Scripts\activate            # Windows
   pip install -r requirements.txt
   copy .env.example .env           # ajustar si tu MySQL tiene contrasena
   python app.py                    # corre en http://127.0.0.1:3007
   ```

### Usuarios de prueba (contrasena de todos: `usat`)

| Correo                         | Rol             |
|--------------------------------|-----------------|
| `admin@usat.edu.pe`            | Administrativo  |
| `seguridad@usat.edu.pe`        | Personal autorizado |

> Solo el personal **Administrativo** y **Personal autorizado** puede entrar al
> panel web. Estudiantes y docentes usaran la app movil.

## Despliegue en la nube (Railway)

La app esta lista para Railway: usa `gunicorn` (ver `Procfile`) y toma toda su
configuracion de variables de entorno (las mismas de `.env.example`).

1. Conectar este repo de GitHub a Railway.
2. Crear una base de datos MySQL y cargar `incidencias_campus.sql`.
3. Definir las variables `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`,
   `DB_PORT`, `DB_SSL`, `SECRET_KEY`.
   - Railway (MySQL interno): `DB_SSL=false`
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
