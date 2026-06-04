"""
Modal de politicas de privacidad y uso responsable.

Usa st.dialog (disponible desde Streamlit 1.35) para mostrar la politica
en un overlay.
- abrir_dialogo_privacidad(): abre el modal completo de 9 secciones (manual).
- show_privacy_dialog_auto(): modal automatico al primer acceso con boton
  "He leido y acepto" obligatorio.
"""

import streamlit as st


@st.dialog("Politica de privacidad y uso responsable", width="large")
def show_privacy_dialog_auto():
    """
    Modal automatico que aparece en el primer acceso.
    Solo se cierra al pulsar 'He leido y acepto'.
    """
    st.markdown(
        """
### Antes de empezar, lee este aviso

Este Asistente Universitario Inteligente es un **prototipo academico**
desarrollado como Trabajo Final de Grado (TFG 2026). No esta destinado
a uso en produccion y no sustituye a los servicios oficiales de
orientacion academica o asistencia psicologica de ninguna universidad.

#### 1. Datos sinteticos

Todos los expedientes, calificaciones y registros academicos pertenecen
a **50 alumnos sinteticos generados algoritmicamente**. No corresponden
a personas reales. Las credenciales son compartidas y publicas dentro
del entorno de demostracion.

#### 2. Procesamiento de mensajes

Los mensajes que escribas se envian a Azure OpenAI (GPT-4o) para su
procesamiento. La conversacion se mantiene en la sesion del navegador
y se pierde al cerrarla. **No se persiste en base de datos**.

#### 3. Logs locales

Se registran eventos de acceso, intentos de violacion de privacidad y
alertas criticas del sistema emocional, todos en archivos locales bajo
`logs/`. No se envian a servidores externos.

#### 4. Sistema emocional

El asistente detecta tres niveles emocionales:
- **Estres academico:** respuesta empatica con recursos universitarios.
- **Malestar emocional no critico:** disclaimer y derivacion firme a
  profesionales humanos.
- **Crisis grave:** respuesta predefinida con telefonos de emergencia
  (024, 112). El sistema no se ofrece como interlocutor en crisis.

El sistema esta sesgado al alza: ante duda, escala de nivel. Esto puede
generar falsos positivos, pero es una decision consciente: preferimos
falsos positivos a falsos negativos en seguridad emocional.

**Si te encuentras en una situacion de crisis personal, contacta con
un profesional sanitario o con el 024 (atencion a la conducta suicida).**

#### 5. Aislamiento por rol

- Un alumno autenticado solo puede consultar SU propio expediente.
- Un administrador puede consultar todos los expedientes.
- Cualquier intento de saltarse el aislamiento queda registrado.

#### 6. Limitaciones declaradas

Como prototipo academico:
- Contrasenas en texto plano (no hash).
- Sin bloqueo por intentos fallidos.
- Sin expiracion de sesion.
- Sin HTTPS forzado (Streamlit local).
- Alertas criticas: solo logs locales, sin email/SMS reales.

#### 7. Contacto

Cualquier consulta sobre este TFG: Felix Garcia, a traves de los
canales academicos correspondientes.

---

*Documento informativo asociado al TFG 2026. No constituye una politica
de privacidad de produccion ni un compromiso legal.*
        """
    )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "He leido y acepto",
            key="btn_accept_privacy_auto",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["privacy_accepted"] = True
            st.rerun()


@st.dialog("Politica de privacidad y uso responsable", width="large")
def _privacy_dialog():
    st.markdown(
        """
### 1. Naturaleza del sistema

Este Asistente Universitario Inteligente es un **prototipo academico**
desarrollado como Trabajo Final de Grado (TFG 2026) en Computacion e
Inteligencia Artificial. **No esta destinado a uso en produccion** ni
sustituye a los servicios oficiales de orientacion academica o asistencia
psicologica de ninguna universidad.

### 2. Datos personales y datos sinteticos

Todos los expedientes, calificaciones, convocatorias y registros academicos
mostrados pertenecen a **50 alumnos sinteticos generados algoritmicamente**
con fines de demostracion. No corresponden a ninguna persona real, viva
o fallecida. Cualquier parecido con datos reales es casual.

Las credenciales de acceso (contrasenas de alumno y administrador) son
**compartidas y publicas** dentro del entorno de demostracion. No deben
considerarse seguras y no se aplican en ningun otro sistema.

### 3. Procesamiento de mensajes

Los mensajes que se escriban en el chat son enviados al servicio de Azure
OpenAI (modelo GPT-4o) para su procesamiento. Azure aplica sus propias
politicas de retencion y filtrado de contenido. Este sistema **no almacena
los mensajes en una base de datos persistente**: la conversacion se
conserva unicamente en la sesion del navegador y se pierde al cerrar
la pestana o cerrar sesion.

### 4. Logs locales

Se registran localmente, en archivos de texto bajo el directorio `logs/`:

- Eventos de acceso (login, logout) con marca de tiempo y rol.
- Intentos de violacion de privacidad entre alumnos (auditoria).
- Alertas criticas del sistema emocional cuando se detecta una crisis grave.

Estos registros **no se transmiten a ningun servidor externo** y existen
solo en la maquina donde se ejecuta el prototipo.

### 5. Sistema de deteccion emocional

El asistente incluye un guardrail con tres niveles emocionales:

- **Nivel 1 (estres academico):** respuesta empatica con sugerencia de
  recursos universitarios.
- **Nivel 2 (malestar emocional no critico):** disclaimer obligatorio y
  derivacion firme a profesionales humanos.
- **Nivel 3 (crisis grave):** respuesta predefinida con recursos de
  emergencia (telefono de la esperanza, 024, 112) y **no se invita** a
  continuar la conversacion con la IA.

El sistema esta deliberadamente sesgado al alza: ante duda, escala de
nivel. Esto puede generar falsos positivos (clasificar como crisis algo
que no lo es) y es una decision consciente: es preferible un falso
positivo a un falso negativo en materia de seguridad emocional.

**Importante:** este sistema no es un servicio de salud mental. Si se
encuentra en una situacion de crisis personal, contacte con un profesional
sanitario o con el telefono de atencion a la conducta suicida 024.

### 6. Aislamiento por rol

El sistema aplica el principio de minimo privilegio en tres capas:

- **Capa SQL:** un alumno autenticado solo puede consultar su propio
  expediente; el agente de datos verifica los permisos antes de cualquier
  consulta.
- **Capa semantica:** el prompt del generador prohibe explicitamente
  revelar datos de otros alumnos a un usuario no administrador.
- **Capa de auditoria:** cualquier intento de saltarse el aislamiento
  queda registrado en el log de accesos.

### 7. Limitaciones declaradas

Como prototipo academico, este sistema asume simplificaciones que no
serian aceptables en produccion:

- Las contrasenas se almacenan en texto plano en variables de entorno
  (en produccion se usaria hash con bcrypt o argon2).
- No existe bloqueo por intentos fallidos.
- No existe expiracion de sesion.
- El acceso es por HTTP local sin HTTPS forzado.
- No se envian notificaciones reales (email/SMS) en caso de alerta
  critica: solo se generan logs locales.

### 8. Trabajo futuro hacia produccion

En un despliegue real serian necesarios, al menos:

- Hash de contrasenas y gestion individualizada de usuarios.
- HTTPS obligatorio y politica de cookies.
- Cifrado en reposo y en transito de cualquier dato sensible.
- Auditoria centralizada con retencion limitada.
- Integracion con servicios oficiales de la universidad (SSO, RGPD,
  comite de etica).
- Notificaciones reales y protocolo de actuacion con los servicios de
  psicologia universitaria.

### 9. Contacto

Cualquier consulta sobre este TFG puede dirigirse al autor del trabajo,
Felix Garcia, a traves de los canales academicos correspondientes.

---

*Documento informativo asociado al TFG 2026. No constituye un compromiso
legal ni una politica de privacidad de produccion.*
        """
    )

    if st.button("Cerrar", key="btn_close_privacy_dialog"):
        st.rerun()


def abrir_dialogo_privacidad():
    """Invocar para abrir el modal. Debe llamarse al pulsar el boton-enlace."""
    _privacy_dialog()
