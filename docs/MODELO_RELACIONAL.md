# Modelo relacional - Base de datos `incidencias_campus`

Motor: **MySQL/MariaDB (InnoDB)** · Charset: **utf8mb4**. El script completo está
en `incidencias_campus.sql` (esquema + datos de prueba).

## 1. Tablas catálogo (listas maestras)

| Tabla | Campos clave | Descripción |
|---|---|---|
| `tipo_usuario` | id, nombre, estado | Roles: Estudiante, Docente, Administrativo, Personal autorizado |
| `area` | id, nombre, estado | Unidades responsables a las que se deriva un caso |
| `categoria` | id, nombre, estado | Emergencia médica, Seguridad, Infraestructura, etc. |
| `urgencia` | id, nombre, estado | Baja, Media, Alta, Crítica |
| `estado` | id, nombre (UNIQUE) | Registrado, En revisión, Derivado, En atención, Resuelto, Cerrado, Rechazado, Reabierto |
| `ubicacion` | id, nombre, tipo, codigo_qr (UNIQUE), latitud, longitud | Aulas/ambientes con QR, zonas de atención y puntos de apoyo |

## 2. Tablas principales

### `usuario`
Datos de la persona. PK `id`. Únicos: `correo_institucional`, `dni`.
Campos: nombres, apellidos, correo_institucional, dni, telefono, **id_tipo_usuario** (FK→tipo_usuario),
contrasenia (hash argon2), imagen, **fcm_token** (push), contacto_emergencia_nombre/telefono, estado, creado_en, actualizado_en.

### `incidencia`
Reporte. PK `id`. FKs: **id_categoria**→categoria, **id_urgencia**→urgencia,
**id_estado**→estado (estado ACTUAL), **id_usuario**→usuario (quien reporta), **id_ubicacion**→ubicacion.
Otros: descripcion (TEXT), latitud/longitud, es_alerta_rapida, fecha, actualizado_en.

### `estado_incidencia` (historial / línea de tiempo - trazabilidad)
Cada fila = un cambio de estado o derivación. PK `id`. FKs: **id_incidencia**→incidencia,
**id_estado**→estado, **id_area**→area (si se deriva), **id_usuario**→usuario (quién hizo el cambio).
Campos: comentario (motivo, p. ej. reapertura), fecha.

## 3. Tablas relacionadas a la incidencia

| Tabla | Relación | Descripción |
|---|---|---|
| `evidencia` | N:1 con incidencia | Varias imágenes por incidencia (req. #4 y #14) |
| `calificacion` | 1:1 con incidencia (UNIQUE) | Puntuación 1..5 (CHECK) + comentario (req. #11) |
| `incidencia_area` | N:M incidencia↔area | Derivaciones a áreas responsables (req. web #3) |
| `mensaje` | N:1 con incidencia y usuario | Chat de la incidencia (req. #10); soporta tipo texto/audio |
| `notificacion` | N:1 con usuario | Historial de avisos (req. #9); estado 0=no leída, 1=leída |
| `recuperacion_contrasenia` | N:1 con usuario | Códigos de recuperación (req. #3); expira_en, usado |

## 4. Diagrama de relaciones (resumen)

```
tipo_usuario --< usuario --< incidencia --< evidencia
                   |             |    |     --< calificacion (1:1)
                   |             |    |     --< incidencia_area >-- area
                   |             |    |     --< mensaje
                   |             |    |     --< estado_incidencia >-- estado / area / usuario
                   |             |   ubicacion
                   |             +-- categoria / urgencia / estado
                   +--< notificacion
                   +--< recuperacion_contrasenia
```

## 5. Reglas de integridad destacadas
- `calificacion`: una sola por incidencia (`UNIQUE`) y puntuación entre 1 y 5 (`CHECK`).
- `ubicacion.codigo_qr`: único (cada QR identifica un solo ambiente).
- Borrado en cascada: al eliminar una incidencia se eliminan sus evidencias, mensajes,
  calificación, derivaciones e historial. Al eliminar un usuario se eliminan sus
  incidencias y notificaciones.
- `id_estado` en `incidencia` usa `ON DELETE RESTRICT` (no se puede borrar un estado en uso).
