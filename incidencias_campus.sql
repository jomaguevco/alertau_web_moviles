-- ==========================================================
--  BASE DE DATOS - APP DE GESTION DE INCIDENCIAS EN CAMPUS
--  Proyecto fin de asignatura - Desarrollo de Apps Moviles
--  Motor: MySQL 8.0 / InnoDB  |  Charset: utf8mb4
-- ----------------------------------------------------------
--  Este archivo CREA la base de datos completa y la llena con
--  datos de prueba para poder usar el panel web de inmediato.
--  Importar desde phpMyAdmin (XAMPP) o con:  mysql < incidencias_campus.sql
--
--  Usuarios de prueba (contrasena de TODOS: 'usat'):
--    admin@usat.edu.pe      -> Administrativo      (entra al panel web)
--    seguridad@usat.edu.pe  -> Personal autorizado (entra al panel web)
--    ana.torres@usat.edu.pe -> Estudiante          (solo app movil)
--    luis.garcia@usat.edu.pe-> Estudiante          (solo app movil)
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
  contrasenia                   VARCHAR(255) NOT NULL,           -- hash argon2
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
-- HISTORIAL / LINEA DE TIEMPO (trazabilidad: web req. #4, reportes #9)
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
-- DATOS SEMILLA
-- ==========================================================

-- Roles (el panel web es solo para id 3 y 4)
INSERT INTO tipo_usuario (id, nombre) VALUES
  (1, 'Estudiante'), (2, 'Docente'), (3, 'Administrativo'), (4, 'Personal autorizado');

-- Areas responsables a las que se deriva una incidencia
INSERT INTO area (id, nombre) VALUES
  (1, 'Seguridad y Vigilancia'),
  (2, 'Mantenimiento e Infraestructura'),
  (3, 'Servicios Generales'),
  (4, 'Topico / Salud'),
  (5, 'Sistemas / TI');

-- Categorias (del documento del proyecto)
INSERT INTO categoria (id, nombre) VALUES
  (1, 'Emergencia medica'), (2, 'Seguridad'), (3, 'Infraestructura'),
  (4, 'Servicios basicos'), (5, 'Objetos perdidos'), (6, 'Laboratorio/Taller'),
  (7, 'Emergencia');  -- categoria generica usada por el boton de alerta rapida (req. #13)

-- Niveles de urgencia
INSERT INTO urgencia (id, nombre) VALUES
  (1, 'Baja'), (2, 'Media'), (3, 'Alta'), (4, 'Critica');

-- Estados del flujo de una incidencia
INSERT INTO estado (id, nombre) VALUES
  (1, 'Registrado'), (2, 'En revision'), (3, 'Derivado'), (4, 'En atencion'),
  (5, 'Resuelto'), (6, 'Cerrado'), (7, 'Rechazado'), (8, 'Reabierto');

-- Ubicaciones del campus (coordenadas aproximadas de USAT, Chiclayo)
INSERT INTO ubicacion (id, nombre, tipo, codigo_qr, latitud, longitud) VALUES
  (1, 'Aula 301 - Edificio Juan Pablo II', 'incidencia',    'QR-A301', -6.71810000, -79.90750000),
  (2, 'Laboratorio de Computo 2',          'incidencia',    'QR-LAB2', -6.71795000, -79.90770000),
  (3, 'Cafeteria Central',                 'incidencia',    'QR-CAFE', -6.71840000, -79.90720000),
  (4, 'Topico / Enfermeria',               'punto_apoyo',   NULL,      -6.71820000, -79.90700000),
  (5, 'Caseta de Seguridad - Puerta 1',    'zona_atencion', NULL,      -6.71880000, -79.90680000);

-- Usuarios. Contrasena de TODOS: 'usat' (hash argon2).
-- Personal que ENTRA al panel web: tipos 3 (Administrativo) y 4 (Personal autorizado).
INSERT INTO usuario (id, nombres, apellidos, correo_institucional, dni, telefono, id_tipo_usuario, contrasenia, estado) VALUES
  (1, 'Carlos', 'Mendoza Diaz',  'admin@usat.edu.pe',      '40111222', '979111222', 3,
      '$argon2id$v=19$m=65536,t=3,p=4$at+CL79Sr0syMFfh8/xRoQ$h9wW/cKgRwIdvzI/sFdvse5A71fQKutksMiXybhvuNc', 1),
  (2, 'Rosa',   'Vega Castro',   'seguridad@usat.edu.pe',  '40222333', '979222333', 4,
      '$argon2id$v=19$m=65536,t=3,p=4$h35/IyYAjF/kZfkbHUl0mA$mJcuaenrBZe0oq4HiQPa85juLZ2L3PgQ3CHViViIT4w', 1),
  (3, 'Ana',    'Torres Lopez',  'ana.torres@usat.edu.pe', '70333444', '987333444', 1,
      '$argon2id$v=19$m=65536,t=3,p=4$RiuEJ9kDiuO8JJjrwp9bzQ$jfvb0TF1EXsQ5R+LBDcd6YgE81mjR76rvAuvMalQWw4', 1),
  (4, 'Luis',   'Garcia Ruiz',   'luis.garcia@usat.edu.pe','70444555', '987444555', 1,
      '$argon2id$v=19$m=65536,t=3,p=4$KMtVif7x7QHIt7S7GZwpzQ$HtLvtSqIBoaYSONmlADqi0DRHZgm2iZeGPNh5npA4PE', 1);

-- Incidencias de ejemplo (para poblar el panel, la lista y los reportes).
-- id_estado: 1=Registrado 2=En revision 3=Derivado 4=En atencion 5=Resuelto 6=Cerrado 7=Rechazado 8=Reabierto
INSERT INTO incidencia (id, descripcion, id_categoria, id_urgencia, id_estado, id_usuario, id_ubicacion, latitud, longitud, es_alerta_rapida, fecha) VALUES
  (1, 'Estudiante con mareos y desmayo en el aula 301.', 1, 4, 4, 3, 1, NULL, NULL, 1, '2026-06-10 08:30:00'),
  (2, 'Proyector del laboratorio de computo no enciende.', 6, 2, 3, 4, 2, NULL, NULL, 0, '2026-06-10 10:15:00'),
  (3, 'Fuga de agua en el bano del segundo piso.', 3, 3, 2, 3, NULL, -6.71800000, -79.90760000, 0, '2026-06-11 09:00:00'),
  (4, 'Persona sospechosa merodeando en el estacionamiento.', 2, 3, 6, 4, 5, NULL, NULL, 0, '2026-06-08 19:40:00'),
  (5, 'Se perdio una mochila azul en la cafeteria.', 5, 1, 1, 3, 3, NULL, NULL, 0, '2026-06-12 13:20:00'),
  (6, 'Corte de energia electrica en el edificio principal.', 4, 3, 5, 4, NULL, -6.71815000, -79.90745000, 0, '2026-06-09 16:05:00');

-- Derivaciones registradas (incidencia -> area)
INSERT INTO incidencia_area (id_incidencia, id_area) VALUES
  (1, 4),   -- emergencia medica -> Topico/Salud
  (2, 5),   -- proyector -> Sistemas/TI
  (4, 1),   -- seguridad -> Seguridad y Vigilancia
  (6, 2);   -- corte de luz -> Mantenimiento

-- Linea de tiempo / trazabilidad de cada incidencia
INSERT INTO estado_incidencia (id_incidencia, id_estado, id_area, id_usuario, comentario, fecha) VALUES
  -- Incidencia 1 (emergencia medica): registrado -> revision -> derivado -> en atencion
  (1, 1, NULL, 3, 'Caso registrado por el estudiante (alerta rapida).', '2026-06-10 08:30:00'),
  (1, 2, NULL, 2, 'Revisado por seguridad, se confirma emergencia.',      '2026-06-10 08:33:00'),
  (1, 3, 4,    2, 'Derivado a Topico / Salud.',                           '2026-06-10 08:35:00'),
  (1, 4, 4,    1, 'Personal de topico atendiendo al estudiante.',        '2026-06-10 08:40:00'),
  -- Incidencia 2 (proyector): registrado -> revision -> derivado
  (2, 1, NULL, 4, 'Caso registrado.',                          '2026-06-10 10:15:00'),
  (2, 2, NULL, 1, 'En revision por el administrador.',         '2026-06-10 11:00:00'),
  (2, 3, 5,    1, 'Derivado a Sistemas / TI.',                 '2026-06-10 11:05:00'),
  -- Incidencia 3 (fuga de agua): registrado -> revision
  (3, 1, NULL, 3, 'Caso registrado.',                          '2026-06-11 09:00:00'),
  (3, 2, NULL, 2, 'En revision.',                              '2026-06-11 09:30:00'),
  -- Incidencia 4 (persona sospechosa): registrado -> ... -> cerrado
  (4, 1, NULL, 4, 'Caso registrado.',                          '2026-06-08 19:40:00'),
  (4, 3, 1,    2, 'Derivado a Seguridad y Vigilancia.',        '2026-06-08 19:42:00'),
  (4, 4, 1,    2, 'Personal de seguridad en sitio.',           '2026-06-08 19:50:00'),
  (4, 5, 1,    2, 'Situacion controlada.',                     '2026-06-08 20:10:00'),
  (4, 6, NULL, 1, 'Caso cerrado.',                             '2026-06-08 20:30:00'),
  -- Incidencia 5 (objeto perdido): registrado
  (5, 1, NULL, 3, 'Caso registrado.',                          '2026-06-12 13:20:00'),
  -- Incidencia 6 (corte de luz): registrado -> derivado -> en atencion -> resuelto
  (6, 1, NULL, 4, 'Caso registrado.',                          '2026-06-09 16:05:00'),
  (6, 3, 2,    1, 'Derivado a Mantenimiento.',                 '2026-06-09 16:10:00'),
  (6, 4, 2,    1, 'Tecnicos revisando el tablero electrico.',  '2026-06-09 16:30:00'),
  (6, 5, 2,    1, 'Energia restablecida.',                     '2026-06-09 17:15:00');

-- Evidencias (las imagenes reales se suben en la app; aqui solo de ejemplo).
INSERT INTO evidencia (id_incidencia, url_imagen) VALUES
  (3, 'ejemplo_fuga.jpg'),
  (6, 'ejemplo_tablero.jpg');

-- Chat / mensajes asociados a una incidencia
INSERT INTO mensaje (id_incidencia, id_usuario, mensaje, fecha) VALUES
  (2, 1, 'Buenos dias, revisaremos el proyector esta tarde.',      '2026-06-10 11:10:00'),
  (2, 4, 'Gracias, estare atento.',                                '2026-06-10 11:20:00'),
  (3, 2, 'Por favor, indique el bano exacto (lado norte o sur).',  '2026-06-11 09:35:00');

-- Calificacion de un caso ya cerrado (req. movil #11)
INSERT INTO calificacion (id_incidencia, puntuacion, comentario) VALUES
  (4, 5, 'Respuesta muy rapida del personal de seguridad.');

-- ==========================================================
-- DIAGRAMA DE RELACIONES
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
