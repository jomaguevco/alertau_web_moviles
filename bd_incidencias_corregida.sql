-- ==========================================================
--  BASE DE DATOS - APP DE GESTION DE INCIDENCIAS EN CAMPUS
--  Proyecto fin de asignatura - Desarrollo de Apps Moviles
--  Motor: MySQL 8.0 / InnoDB  |  Charset: utf8mb4
--  Version corregida: 2026-06-03
-- ==========================================================
--  Cambios respecto al esquema original:
--   * Todas las columnas 'fecha' VARCHAR -> DATETIME
--   * Charset utf8mb3 -> utf8mb4 (soporte emojis en chat/comentarios)
--   * Catalogo 'estado' para estados con nombre
--   * Tabla 'estado_incidencia' = historial / linea de tiempo
--   * Tabla 'recuperacion_contrasenia' (req. movil #3)
--   * usuario: fcm_token + contacto de emergencia (req. #9 y #12)
--   * incidencia: es_alerta_rapida, descripcion TEXT, coords DECIMAL
--   * calificacion: UNIQUE por incidencia + CHECK 1..5
--   * ubicacion: campo 'tipo' (zonas de atencion / puntos de apoyo)
--   * Coordenadas unificadas a DECIMAL, naming de FKs uniforme
-- ==========================================================

DROP DATABASE IF EXISTS incidencias_campus;
CREATE DATABASE incidencias_campus
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE incidencias_campus;

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------
-- CATALOGOS / MAESTROS
-- ----------------------------------------------------------

-- Roles: estudiante, docente, administrativo, personal autorizado...
CREATE TABLE tipo_usuario (
  id     INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  estado TINYINT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Areas / unidades responsables a las que se deriva un caso
CREATE TABLE area (
  id     INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  estado TINYINT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Categorias: emergencia medica, seguridad, infraestructura,
-- servicios basicos, objetos perdidos, laboratorio/taller
CREATE TABLE categoria (
  id     INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  estado TINYINT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Niveles de urgencia: baja, media, alta, critica...
CREATE TABLE urgencia (
  id     INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(15) NOT NULL,
  estado TINYINT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Catalogo de estados del flujo de una incidencia
-- registrado, en revision, derivado, en atencion, resuelto,
-- cerrado, rechazado, reabierto
CREATE TABLE estado (
  id     INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(30) NOT NULL,
  estado TINYINT DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_estado_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ubicaciones del campus (con QR) y tambien zonas de atencion / puntos de apoyo
CREATE TABLE ubicacion (
  id        INT NOT NULL AUTO_INCREMENT,
  nombre    VARCHAR(100) NOT NULL,
  tipo      VARCHAR(30) NOT NULL DEFAULT 'incidencia',  -- incidencia | zona_atencion | punto_apoyo
  codigo_qr VARCHAR(255) DEFAULT NULL,                  -- NULL para zonas/puntos sin QR
  latitud   DECIMAL(10,8) NOT NULL,
  longitud  DECIMAL(11,8) NOT NULL,
  estado    TINYINT DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ubicacion_qr (codigo_qr)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- USUARIOS
-- ----------------------------------------------------------
CREATE TABLE usuario (
  id                            INT NOT NULL AUTO_INCREMENT,
  nombres                       VARCHAR(100) NOT NULL,
  apellidos                     VARCHAR(100) NOT NULL,
  correo_institucional          VARCHAR(100) NOT NULL,
  dni                           VARCHAR(20) NOT NULL,
  telefono                      VARCHAR(20) DEFAULT NULL,
  id_tipo_usuario               INT DEFAULT NULL,
  contrasenia                   VARCHAR(255) NOT NULL,           -- hash
  imagen                        TEXT,
  fcm_token                     VARCHAR(255) DEFAULT NULL,       -- push Firebase (req. #9)
  contacto_emergencia_nombre    VARCHAR(100) DEFAULT NULL,       -- perfil (req. #12)
  contacto_emergencia_telefono  VARCHAR(20)  DEFAULT NULL,
  estado                        TINYINT DEFAULT 1,
  creado_en                     DATETIME DEFAULT CURRENT_TIMESTAMP,
  actualizado_en                DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuario_correo (correo_institucional),
  UNIQUE KEY uq_usuario_dni (dni),
  CONSTRAINT fk_usuario_tipo FOREIGN KEY (id_tipo_usuario)
    REFERENCES tipo_usuario (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Codigos / tokens de recuperacion de contrasena (req. movil #3)
CREATE TABLE recuperacion_contrasenia (
  id         INT NOT NULL AUTO_INCREMENT,
  id_usuario INT NOT NULL,
  codigo     VARCHAR(255) NOT NULL,
  expira_en  DATETIME NOT NULL,
  usado      TINYINT DEFAULT 0,
  creado_en  DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_recup_usuario (id_usuario),
  CONSTRAINT fk_recup_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- INCIDENCIA (tabla principal)
-- ----------------------------------------------------------
CREATE TABLE incidencia (
  id               INT NOT NULL AUTO_INCREMENT,
  descripcion      TEXT NOT NULL,
  id_categoria     INT DEFAULT NULL,
  id_urgencia      INT DEFAULT NULL,
  id_estado        INT NOT NULL,                       -- estado ACTUAL (FK a catalogo estado)
  id_usuario       INT NOT NULL,                       -- quien reporta
  id_ubicacion     INT DEFAULT NULL,                   -- si se uso QR
  latitud          DECIMAL(10,8) DEFAULT NULL,         -- si se uso GPS / mapa
  longitud         DECIMAL(11,8) DEFAULT NULL,
  es_alerta_rapida TINYINT DEFAULT 0,                  -- boton de alerta rapida (req. #13)
  fecha            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_incidencia_estado (id_estado),
  KEY idx_incidencia_fecha (fecha),
  KEY idx_incidencia_categoria (id_categoria),
  KEY idx_incidencia_urgencia (id_urgencia),
  CONSTRAINT fk_incidencia_categoria FOREIGN KEY (id_categoria)
    REFERENCES categoria (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_incidencia_urgencia FOREIGN KEY (id_urgencia)
    REFERENCES urgencia (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_incidencia_estado FOREIGN KEY (id_estado)
    REFERENCES estado (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_incidencia_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_incidencia_ubicacion FOREIGN KEY (id_ubicacion)
    REFERENCES ubicacion (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- HISTORIAL / LINEA DE TIEMPO (req. movil #7, #8 y web #4, reportes #9)
-- Cada fila = un cambio de estado o derivacion, con quien y cuando.
-- Sirve tambien para reapertura (estado 'reabierto' + comentario = motivo).
-- ----------------------------------------------------------
CREATE TABLE estado_incidencia (
  id            INT NOT NULL AUTO_INCREMENT,
  id_incidencia INT NOT NULL,
  id_estado     INT NOT NULL,                  -- estado al que pasa
  id_area       INT DEFAULT NULL,              -- area a la que se deriva (si aplica)
  id_usuario    INT DEFAULT NULL,              -- quien realizo el cambio (trazabilidad)
  comentario    VARCHAR(255) DEFAULT NULL,     -- nota / motivo (p.ej. reapertura)
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_hist_incidencia (id_incidencia),
  KEY idx_hist_fecha (fecha),
  CONSTRAINT fk_hist_incidencia FOREIGN KEY (id_incidencia)
    REFERENCES incidencia (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_hist_estado FOREIGN KEY (id_estado)
    REFERENCES estado (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_hist_area FOREIGN KEY (id_area)
    REFERENCES area (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_hist_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- TABLAS RELACIONADAS A INCIDENCIA
-- ----------------------------------------------------------

-- Multiples evidencias por incidencia (req. movil #4 y #14)
CREATE TABLE evidencia (
  id            INT NOT NULL AUTO_INCREMENT,
  id_incidencia INT NOT NULL,
  url_imagen    VARCHAR(255) NOT NULL,
  creado_en     DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_evidencia_incidencia (id_incidencia),
  CONSTRAINT fk_evidencia_incidencia FOREIGN KEY (id_incidencia)
    REFERENCES incidencia (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Calificacion: 1 por incidencia cerrada (req. movil #11)
CREATE TABLE calificacion (
  id            INT NOT NULL AUTO_INCREMENT,
  id_incidencia INT NOT NULL,
  puntuacion    INT NOT NULL,
  comentario    VARCHAR(255) DEFAULT NULL,
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_calificacion_incidencia (id_incidencia),
  CONSTRAINT chk_puntuacion CHECK (puntuacion BETWEEN 1 AND 5),
  CONSTRAINT fk_calificacion_incidencia FOREIGN KEY (id_incidencia)
    REFERENCES incidencia (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Derivacion de incidencia a areas (req. web #3)
CREATE TABLE incidencia_area (
  id            INT NOT NULL AUTO_INCREMENT,
  id_incidencia INT NOT NULL,
  id_area       INT NOT NULL,
  estado        TINYINT NOT NULL DEFAULT 1,
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_inc_area_incidencia (id_incidencia),
  CONSTRAINT fk_inc_area_area FOREIGN KEY (id_area)
    REFERENCES area (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_inc_area_incidencia FOREIGN KEY (id_incidencia)
    REFERENCES incidencia (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat asociado a la incidencia (req. movil #10 / web #7)
-- tipo/url_audio incluidos para el extra de equipos de 6 (audio en chat)
CREATE TABLE mensaje (
  id            INT NOT NULL AUTO_INCREMENT,
  id_incidencia INT NOT NULL,
  id_usuario    INT NOT NULL,
  mensaje       VARCHAR(255) NOT NULL,
  tipo          ENUM('texto','audio') NOT NULL DEFAULT 'texto',
  url_audio     VARCHAR(255) DEFAULT NULL,
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_mensaje_incidencia (id_incidencia),
  CONSTRAINT fk_mensaje_incidencia FOREIGN KEY (id_incidencia)
    REFERENCES incidencia (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_mensaje_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Historial de notificaciones enviadas (req. movil #9)
CREATE TABLE notificacion (
  id         INT NOT NULL AUTO_INCREMENT,
  id_usuario INT NOT NULL,
  mensaje    VARCHAR(255) NOT NULL,
  fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado     TINYINT NOT NULL DEFAULT 0,    -- 0=no leida, 1=leida
  PRIMARY KEY (id),
  KEY idx_notificacion_usuario (id_usuario),
  CONSTRAINT fk_notificacion_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================================
-- DATOS SEMILLA (catalogos del PDF)
-- ==========================================================
INSERT INTO tipo_usuario (nombre) VALUES
  ('Estudiante'), ('Docente'), ('Administrativo'), ('Personal autorizado');

INSERT INTO categoria (nombre) VALUES
  ('Emergencia medica'), ('Seguridad'), ('Infraestructura'),
  ('Servicios basicos'), ('Objetos perdidos'), ('Laboratorio/Taller');

INSERT INTO urgencia (nombre) VALUES
  ('Baja'), ('Media'), ('Alta'), ('Critica');

INSERT INTO estado (nombre) VALUES
  ('Registrado'), ('En revision'), ('Derivado'), ('En atencion'),
  ('Resuelto'), ('Cerrado'), ('Rechazado'), ('Reabierto');

-- ==========================================================
-- DIAGRAMA DE RELACIONES (actualizado)
-- ==========================================================
-- tipo_usuario --< usuario --< incidencia --< evidencia
--                    |            |    |     --< calificacion (1:1)
--                    |            |    |     --< incidencia_area >-- area
--                    |            |    |     --< mensaje
--                    |            |    |     --< estado_incidencia >-- estado / area / usuario
--                    |            |  ubicacion
--                    |            +-- categoria / urgencia / estado
--                    +--< notificacion
--                    +--< recuperacion_contrasenia
-- ==========================================================
