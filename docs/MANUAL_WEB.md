# Manual de usuario - Panel Web AlertaU

Panel para el **personal autorizado** del campus (Administrativo y Personal
autorizado). Permite gestionar las incidencias reportadas desde la app móvil.

## 1. Acceso
1. Abrir la URL del panel (ej. `https://alertau-web-production.up.railway.app`).
2. Ingresar **correo institucional** y **contraseña**.
   - Usuarios de prueba (clave `usat`): `admin@usat.edu.pe`, `seguridad@usat.edu.pe`.
3. Solo el personal autorizado puede entrar; estudiantes/docentes usan la app móvil.

## 2. Panel resumen (inicio)
Muestra indicadores clave: total de incidencias, casos críticos, casos abiertos,
% de casos cerrados, y conteos por tipo, urgencia y estado.

## 3. Gestión de incidencias
- Menú **Incidencias**: tabla con todas las incidencias.
- **Filtros**: por estado, tipo (categoría), urgencia, área y rango de fechas.
  Pulsa *Filtrar* para aplicar y *Limpiar* para quitarlos.
- Botón **Ver** para abrir el detalle.

## 4. Detalle de una incidencia
- **Datos completos**: descripción, tipo, urgencia, reportante, ubicación,
  coordenadas (con enlace a Google Maps) y fecha.
- **Evidencias**: miniaturas de las fotos adjuntas (clic para ampliar).
- **Cambiar estado** (con trazabilidad): elige el nuevo estado, agrega un
  comentario opcional y guarda. Queda registrado en la línea de tiempo y se
  notifica al usuario que reportó.
- **Derivar a un área**: selecciona el área responsable; el estado pasa a
  "Derivado" y se notifica al usuario.
- **Línea de tiempo**: historial de cambios (estado, área, responsable, fecha).
- **Chat de seguimiento**: enviar mensajes al usuario sobre el caso.

## 5. Gestión de usuarios
- Menú **Usuarios**: lista de todos los usuarios con su rol y estado.
- Botón **Dar de baja / Activar** para habilitar o deshabilitar una cuenta.

## 6. Cerrar sesión
Botón **Salir** en la barra superior.
