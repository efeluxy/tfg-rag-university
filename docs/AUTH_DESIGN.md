# Diseño del Sistema de Autenticación con 3 Roles

**Proyecto:** Asistente Universitario Inteligente con RAG  
**Alumno:** Félix García  
**Versión:** 1.0 — Junio 2026  

---

## 1. Introducción y Motivación

El asistente universitario gestiona información sensible: expedientes académicos con notas, créditos, estado de riesgo académico, becas activas y datos personales de estudiantes. Permitir el acceso irrestricto a esta información —o peor, sin siquiera saber quién está accediendo— sería una vulnerabilidad grave tanto desde el punto de vista técnico como legal.

La implementación de un sistema de control de acceso es, por tanto, una necesidad funcional y ética del proyecto. Los objetivos concretos que motivan el diseño son:

1. **Proteger la privacidad** de los expedientes académicos, limitando el acceso a la propia información del alumno autenticado.
2. **Distinguir el contexto de uso**: un invitado (potencial alumno, familiar) no debería ver datos personales ajenos, mientras que un administrador (personal de orientación) necesita acceso completo.
3. **Registrar el acceso** para auditoría, especialmente en un sistema que puede generar alertas de salud mental (ver `EMOTIONAL_GUARDRAIL_DESIGN.md`).
4. **Simplidad de implementación** acorde al alcance académico del TFG, sin comprometer la comprensión de los principios de seguridad que se documenten.

### Por qué 3 roles y no más ni menos

Se descartó un modelo con **un solo rol** porque no permite diferenciar el acceso público del personal y el administrativo, perdiendo toda granularidad. Se descartó un modelo con **más de 3 roles** (por ejemplo, profesor, tutor, coordinador de grado) porque añadiría complejidad de gestión sin aportar valor demostrable dentro del ámbito del TFG. La terna **invitado/alumno/admin** representa exactamente los tres perfiles de usuario real de un asistente universitario demo.

---

## 2. Arquitectura de Roles

### 2.1 Tabla de permisos por rol

| Funcionalidad | Invitado | Alumno | Admin |
|---|---|---|---|
| Acceso al chat | ✓ | ✓ | ✓ |
| Información pública (corpus) | ✓ | ✓ | ✓ |
| Ver su propio expediente | — | ✓ (fijo) | ✓ |
| Ver expediente de otros | — | — | ✓ |
| Selector de alumno en sidebar | — | — | ✓ |
| Cambiar de identidad | — | — | ✓ |
| Cerrar sesión | ✓ | ✓ | ✓ |
| Limpiar conversación | ✓ | ✓ | ✓ |

### 2.2 Diagrama de flujo de autenticación

```
Arranque de la app (main.py)
         |
         v
st.session_state.authenticated == False?
         |
    SÍ   |    NO
         |     └──> App principal (sidebar + chat + grafo)
         v
   render_login()
         |
    ┌────┴──────────────────────────────┐
    │   3 tabs en la pantalla de login  │
    └────┬──────────┬────────────────────┘
         │          │                   │
    [Alumno]   [Invitado]          [Admin]
         │          │                   │
  select + pwd  click botón       solo pwd
         │          │                   │
  authenticate_  _start_session    authenticate_
  student()      (guest, None)     admin()
         │                              │
  True?  │                       True? │
   ├── SI: _start_session(student, uid) │
   └── NO: st.error()         ├── SI: _start_session(admin, None)
                               └── NO: st.error()
         │
         v
  st.session_state.authenticated = True
  st.rerun()  →  App principal
```

### 2.3 Decisión de diseño: alumno fija su identidad al login

A diferencia del admin, el alumno no puede cambiar de identidad una vez autenticado. Esta decisión responde a dos principios:

1. **Integridad del expediente**: permitir cambio de identidad sin re-autenticación violaría el modelo de seguridad (un alumno podría acceder al expediente de otro sin conocer la contraseña).
2. **Simplicidad del modelo**: dado que la contraseña es compartida entre todos los alumnos (decisión consciente para la demo), el único mecanismo de control de identidad es la sesión iniciada. La identidad queda fijada en `st.session_state.authenticated_user_id` y el sidebar la impone en cada render.

---

## 3. Almacenamiento de Credenciales

### 3.1 Decisión: variables de entorno (.env) en texto plano

Las contraseñas se almacenan en el archivo `.env` como valores en claro:

```
STUDENT_PASSWORD=alumno2026
ADMIN_PASSWORD=admin2026
```

La lectura se realiza mediante `os.getenv()` tras cargar el archivo con `python-dotenv`. El archivo `.env` está incluido en `.gitignore` y nunca se commitea al repositorio.

### 3.2 Por qué es suficiente para una demo académica

En el contexto del TFG, esta implementación es suficiente porque:

- Los datos de alumnos son **sintéticos** (generados con `scripts/generate_students.py`), no corresponden a personas reales.
- El sistema se ejecuta **localmente** en la máquina del desarrollador, sin exposición a redes públicas durante las demostraciones.
- El objetivo es demostrar la **arquitectura funcional** del control de acceso, no implementar seguridad de producción.
- El evaluador puede verificar el comportamiento sin riesgo de comprometer datos reales.

### 3.3 Por qué es INADECUADO para producción

Almacenar contraseñas en texto plano en variables de entorno es inadecuado en producción por las siguientes razones:

1. **Sin hash**: si el archivo `.env` o los logs se filtran, las contraseñas quedan expuestas directamente.
2. **Contraseña compartida**: todos los alumnos tienen la misma contraseña, lo que impide rastrear qué alumno específico realizó cada acceso (no repudio).
3. **Sin rotación**: no existe mecanismo para cambiar la contraseña periódicamente o tras una brecha.
4. **Sin separación de secretos**: las credenciales de la base de datos, Azure y la autenticación conviven en el mismo archivo.
5. **Sin cifrado en reposo**: el archivo `.env` en disco no está cifrado.

---

## 4. Limitaciones Reconocidas

El sistema en su versión 1.0 presenta las siguientes limitaciones explícitas, reconocidas conscientemente como decisiones de diseño para el alcance del TFG:

1. **Sin hash de contraseñas**: No se usa bcrypt, argon2 ni ningún algoritmo de hash. Las contraseñas se comparan en texto plano mediante `==`.

2. **Contraseña compartida entre los 50 alumnos**: La variable `STUDENT_PASSWORD` es única para todos los estudiantes. Esto significa que cualquier alumno conocedor de la contraseña podría iniciar sesión como cualquier otro alumno. En producción, cada alumno tendría su propia credencial.

3. **Sin expiración de sesión**: Una vez autenticado, el estado de sesión de Streamlit (`st.session_state`) persiste indefinidamente mientras el navegador esté abierto. No existe timeout por inactividad.

4. **Sin HTTPS forzado**: Streamlit por defecto sirve sobre HTTP. En producción, todas las comunicaciones deben ir sobre HTTPS/TLS para proteger las credenciales en tránsito.

5. **Sin rate limiting ni bloqueo por intentos**: No existe protección contra ataques de fuerza bruta. Un atacante puede intentar contraseñas ilimitadas sin consecuencia.

6. **Sin autenticación de doble factor (2FA)**: El admin en particular debería requerir 2FA en producción, dado que tiene acceso a todos los expedientes y puede leer el historial de alertas de salud mental.

7. **Sin recuperación de contraseña**: No existe flujo de "olvidé mi contraseña" ni mecanismo de reseteo.

8. **Sesión no persistente entre recargas**: Si el usuario recarga el navegador, `st.session_state` se pierde y debe volver a autenticarse. Esto es un comportamiento estándar de Streamlit sin backend de sesiones persistente.

---

## 5. Trazabilidad y Auditoría

### 5.1 logs/access.log

Cada intento de acceso —exitoso o fallido— se registra en `logs/access.log` en formato JSONL (una entrada JSON por línea):

```json
{"timestamp": "2026-06-01T10:30:00.000000Z", "role": "student", "user_id": "ALU001", "success": true, "session_id": "uuid-de-sesion"}
{"timestamp": "2026-06-01T10:31:00.000000Z", "role": "admin", "user_id": null, "success": false, "session_id": null}
```

### 5.2 Información registrada

Por cada acceso se registra:
- `timestamp`: Marca temporal UTC (ISO 8601).
- `role`: Rol intentado (`guest`, `student`, `admin`).
- `user_id`: ID del alumno para logins de tipo student; null para guest y admin.
- `success`: Booleano que indica si el login fue exitoso.
- `session_id`: UUID de la sesión creada (null si el login falló).

### 5.3 Limitaciones del logging actual

- El log se escribe en disco local. En producción, los logs de seguridad deben enviarse a un SIEM (Security Information and Event Management) centralizado.
- No se registra la dirección IP del cliente (Streamlit no expone esta información fácilmente).
- No se implementa rotación de logs (el archivo crece indefinidamente).
- Los logs pueden ser modificados por cualquier usuario con acceso al sistema de archivos local.

---

## 6. Trabajo Futuro / Para Producción

Las siguientes mejoras son necesarias antes de desplegar el sistema en un entorno real con datos de estudiantes reales:

### 6.1 Hash seguro de contraseñas

Implementar hashing con **bcrypt** o **argon2** para todas las contraseñas almacenadas. Ejemplo con Python:

```python
import bcrypt

# Al crear la contraseña:
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Al verificar:
bcrypt.checkpw(password_input.encode(), hashed)
```

### 6.2 Base de datos de usuarios separada

Crear una tabla `users` en SQLite (o en una base de datos separada) con campos `user_id`, `hashed_password`, `role`, `created_at`, `last_login`, en lugar de almacenar credenciales en `.env`.

### 6.3 Tokens de sesión JWT con expiración

Reemplazar `st.session_state.authenticated` por tokens JWT firmados con una clave secreta, incluyendo `exp` (expiración), `iat` (fecha de emisión) y `sub` (user_id). Esto permite sesiones con tiempo de vida limitado y verificación sin estado del servidor.

### 6.4 HTTPS obligatorio

Configurar Streamlit para servir exclusivamente sobre HTTPS usando un proxy inverso (Nginx, Traefik) con certificado TLS válido. Nunca exponer el puerto de Streamlit directamente.

### 6.5 Rate limiting y bloqueo por intentos

Implementar un contador de intentos fallidos por IP/user_id. Tras N intentos fallidos (por ejemplo, 5), bloquear la cuenta por un período de tiempo (bloqueo progresivo: 1 min, 5 min, 30 min) o indefinidamente hasta desbloqueo manual.

### 6.6 Autenticación de doble factor (2FA) para admin

Exigir un segundo factor (TOTP via Google Authenticator, o código enviado por email/SMS) para el rol de admin, dado su acceso privilegiado a datos sensibles.

### 6.7 Política de contraseñas

Imponer requisitos mínimos: longitud >= 12 caracteres, combinación de mayúsculas, minúsculas, números y símbolos. Rechazar contraseñas comunes mediante diccionario.

### 6.8 Flujo de recuperación de contraseña

Implementar flujo de "olvidé mi contraseña" con envío de enlace de reseteo único y caducado (por ejemplo, válido 15 minutos) al email institucional del alumno.

### 6.9 Auditoría externa y SIEM

Enviar todos los eventos de autenticación a un sistema centralizado (por ejemplo, Splunk, ELK Stack, o Azure Monitor) para análisis de amenazas, detección de anomalías y cumplimiento del RGPD.

---

## 7. Justificación Académica

Este sistema de autenticación cumple con los requisitos del Trabajo de Fin de Grado por las siguientes razones:

**Funcionalidad completa demostrable**: Los tres roles están completamente implementados y son operativos. Se puede verificar interactivamente que cada rol accede exactamente a lo que debe acceder y nada más.

**Separación clara entre demo y producción**: El documento documenta explícitamente las limitaciones y el camino hacia una implementación productiva, demostrando comprensión profunda de los principios de seguridad aunque no todos se implementen en el prototipo.

**Equilibrio coherente**: Implementar bcrypt, JWT, 2FA y rate limiting requeriría infraestructura adicional (backend dedicado, base de datos de usuarios, servidor de emails) que excede el alcance de un TFG cuyo foco es la arquitectura RAG multi-agente. El sistema de autenticación es un componente de soporte, no el objeto principal de estudio.

**Trazabilidad**: La existencia de `logs/access.log` demuestra conciencia sobre la importancia de la auditoría, aunque la implementación sea básica.

**Documentación del riesgo**: Documentar las limitaciones conocidas es más valioso académicamente que implementar seguridad sin entender sus fundamentos. El evaluador puede verificar que el alumno conoce exactamente qué está sacrificando y por qué.

---

*Documento elaborado como parte de la memoria del Trabajo de Fin de Grado. Para el diseño del sistema de detección emocional con alertas críticas, ver `docs/EMOTIONAL_GUARDRAIL_DESIGN.md`.*
