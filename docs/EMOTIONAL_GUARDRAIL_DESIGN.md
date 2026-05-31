# Diseño del Sistema de Guardrail Emocional en 3 Niveles

**Proyecto:** Asistente Universitario Inteligente con RAG  
**Alumno:** Félix García  
**Versión:** 1.0 — Mayo 2026  

---

## 1. Introducción y Motivación

Los asistentes conversacionales basados en inteligencia artificial se despliegan cada vez más en contextos institucionales donde los usuarios —en este caso, estudiantes universitarios— pueden encontrarse en situaciones de vulnerabilidad emocional. Un chatbot académico no puede ignorar las señales de malestar emocional de los usuarios, pero tampoco puede actuar como un sustituto de la atención psicológica profesional.

La salud mental en el ámbito universitario es una preocupación creciente. Según informes de organismos como la Organización Mundial de la Salud (OMS) y estudios publicados por universidades europeas, entre el 20% y el 30% de los estudiantes experimentan síntomas de ansiedad o depresión durante sus estudios. En España, la Confederación de Salud Mental España señala que la etapa universitaria concentra una alta incidencia de primeros episodios de malestar psicológico severo, especialmente en los primeros cursos.

Ante esta realidad, el presente sistema implementa un **Guardrail Emocional de 3 Niveles** que permite al asistente:

1. Detectar automáticamente el estado emocional del estudiante a partir de su mensaje.
2. Adaptar la respuesta al nivel de severidad detectado (acompañamiento leve, derivación con disclaimer, o derivación urgente con alerta automática).
3. Registrar automáticamente un reporte cuando se detecta una situación de crisis grave, para que el Servicio de Orientación Psicológica de la institución pueda actuar de forma proactiva.

Este sistema representa una mejora fundamental respecto al modelo binario anterior (guardrail activado/no activado), que trataba toda señal emocional de forma homogénea y no diferenciaba entre un estudiante agobiado por los exámenes y uno en riesgo vital inmediato.

---

## 2. Diseño en 3 Niveles (Tiers Emocionales)

### 2.1 Por qué 3 niveles y no 2

El modelo binario previo (triggered=True/False) presentaba dos problemas fundamentales:

- **Sobreactivación**: Mensajes de estrés académico normal (muy frecuentes) activaban el guardrail de la misma forma que una crisis grave, interrumpiendo innecesariamente el flujo de la conversación.
- **Infravaloración**: Al existir una sola categoría de "crisis emocional", el sistema no podía graduar su respuesta. La respuesta era idéntica para el estudiante nervioso por un examen y para uno con ideación suicida.

El modelo de 3 niveles resuelve ambos problemas: permite acompañar de forma natural (tier 1), derivar con cuidado (tier 2) y actuar con urgencia (tier 3), sin interrumpir el flujo en los casos menos graves.

### 2.2 Tabla de Tiers

| Tier | Etiqueta | Criterios | Comportamiento | ¿Activa guardrail? |
|------|----------|-----------|----------------|-------------------|
| **0** | (ninguno) | Mensajes neutros, académicos, administrativos, saludos | Flujo normal del asistente | No |
| **1** | `academic_stress` | Estrés académico normal: agobio por exámenes, sobrecarga, ansiedad por entregas | Respuesta empática + consejos prácticos + mención del servicio psicológico como recurso | No |
| **2** | `emotional_distress` | Malestar emocional no crítico: tristeza prolongada, soledad, desmotivación, agotamiento | Respuesta empática + disclaimer obligatorio (IA ≠ profesional) + derivación firme al servicio psicológico | No |
| **3** | `crisis_grave` | Ideación suicida, autolesión, desesperanza extrema, cualquier indicador de riesgo vital | Respuesta predefinida con recursos de emergencia. NO invita a continuar con la IA. | **Sí** — genera alerta crítica automática |

### 2.3 Diagrama ASCII del Flujo de Decisión

```
Usuario envía mensaje
        |
        v
   [Router] → clasifica intent
        |
        v
   [Guardrail]
        |
        |── intent == EMOTIONAL_SUPPORT?
        |         |
        |         v
        |    [Tier Classifier LLM]
        |         |
        |         |── Tier 0: sin malestar → [Retriever] → [Generator]
        |         |── Tier 1: academic_stress → [Retriever] → [Generator + tier1 section]
        |         |── Tier 2: emotional_distress → [Retriever] → [Generator + tier2 section]
        |         └── Tier 3: crisis_grave → [Generator BYPASS] → respuesta predefinida
        |                                           |
        |                                           v
        |                                   [ALERTA CRITICA]
        |                                   data/alerts/*.json
        |                                   logs/critical_alerts.log
        |
        └── intent != EMOTIONAL_SUPPORT
                  |
                  v
             [Out-of-scope check LLM]
                  |
                  |── out_of_scope / inappropriate → [Generator] → respuesta predefinida
                  └── no triggered → [Retriever] → [Generator]
```

---

## 3. Sistema de Alertas Críticas

### 3.1 Cuándo se dispara

Una alerta crítica se genera **únicamente cuando el clasificador de tiers emocionales devuelve Tier 3 (crisis_grave)**. Esta clasificación se produce cuando el mensaje del usuario contiene indicadores de:

- Ideación suicida explícita o implícita.
- Menciones de autolesión como "salida" o "solución".
- Desesperanza extrema con deseo de desaparecer.
- Cualquier formulación que sugiera riesgo vital inmediato.

El clasificador está diseñado con una **política de falso positivo preferido**: ante ambigüedad entre tier 2 y tier 3, el sistema clasifica siempre como tier 3. Un falso positivo genera una alerta innecesaria; un falso negativo puede costar una vida.

### 3.2 Qué información se registra

Cada alerta contiene:

- `alert_id`: Identificador único (formato `ALERT-YYYYMMDD-HHMMSS-<uuid8>`).
- `timestamp`: Marca temporal UTC en formato ISO 8601.
- `severity`: Siempre `"CRITICAL"` para alertas tier 3.
- `trigger_message`: El mensaje exacto del usuario que disparó la alerta.
- `session_id`: Identificador de la sesión de conversación.
- `student`: Datos del alumno si está identificado (nombre, email, grado, año, GPA, estado académico). Si es anónimo, `identified: false`.
- `conversation_context`: Los últimos 3 turnos de conversación (máximo 6 mensajes, limitados a 500 caracteres por mensaje).
- `recommended_action`: Protocolo de actuación recomendado para el equipo psicológico.
- `alert_destination`: Datos de contacto del servicio receptor.
- `system_metadata`: Versión del módulo y canales utilizados/pendientes.

### 3.3 Estructura del archivo JSON de alerta

```json
{
  "alert_id": "ALERT-20260531-143022-a1b2c3d4",
  "timestamp": "2026-05-31T14:30:22.000000Z",
  "severity": "CRITICAL",
  "detected_tier": 3,
  "tier_label": "crisis_grave",
  "rationale": "El mensaje contiene indicacion directa de ideacion suicida",
  "trigger_message": "No quiero seguir viviendo, no puedo mas",
  "session_id": "uuid-de-sesion",
  "student": {
    "user_id": "ALU042",
    "identified": true,
    "name": "Nombre Apellido",
    "email": "alumno@universidad.es",
    "degree": "Ingenieria Informatica",
    "year": 3,
    "academic_status": "at_risk",
    "gpa": 5.2
  },
  "conversation_context": [...],
  "recommended_action": "Contacto inmediato...",
  "alert_destination": {
    "primary": "psicologia@universidad.es",
    "phone": "900 456 789",
    "emergency_fallback": "024"
  },
  "system_metadata": {
    "graph_version": "1.0",
    "alert_module_version": "1.0",
    "channels_used": ["log", "json_file"],
    "channels_pending": ["email", "sms", "phone_call"]
  }
}
```

### 3.4 Canales actuales y futuros

**Canales activos (v1.0 TFG):**
- Archivo JSON individual en `data/alerts/ALERT-*.json`.
- Línea JSONL en `logs/critical_alerts.log`.

**Canales preparados para producción (fuera del alcance del TFG):**
- Envío de email al servicio psicológico (SMTP/SendGrid).
- SMS urgente al personal de guardia (Twilio).
- Llamada automática al teléfono del alumno si está identificado.
- Webhook a canal Slack/Teams del equipo psicológico.

---

## 4. Consideraciones Éticas

### 4.1 Safe Messaging Guidelines aplicadas

El diseño del sistema sigue las directrices de Safe Messaging Guidelines publicadas por organizaciones como AFSP (American Foundation for Suicide Prevention) y adaptadas al contexto europeo. En concreto:

- **No descripciones de métodos**: La respuesta predefinida para tier 3 no menciona métodos de autolesión ni aporta información que pudiera ser utilizada de forma dañina.
- **No minimización ni amplificación**: El sistema no resta importancia al malestar, pero tampoco lo dramatiza. La respuesta transmite calma y urgencia de forma equilibrada.
- **Derivación a profesionales**: En ningún caso el asistente se ofrece como interlocutor suficiente. La derivación es la acción central de la respuesta.
- **Recursos de emergencia siempre visibles**: La línea 024 y el número de emergencias 112 aparecen siempre en la respuesta de tier 3, dado que cualquier canal puede ser el que salve una vida.

### 4.2 Por qué la IA NO se ofrece como interlocutor en tier 3

En situaciones de crisis grave, ofrecer la IA como "alguien con quien hablar" podría:

1. **Retrasar la búsqueda de ayuda real**: Si el usuario percibe que ya "ha hablado con alguien", puede reducir la urgencia de contactar a un profesional.
2. **Crear una falsa sensación de contención**: La IA no tiene capacidad de intervención en crisis, no puede llamar a emergencias, ni evaluar el riesgo real.
3. **Generar dependencia peligrosa**: En situaciones agudas, el vínculo emocional con una IA podría ser contraproducente.

Por estos motivos, la respuesta de tier 3 es **predefinida, fija e invariable**: no pasa por el LLM generativo y siempre contiene los mismos recursos de emergencia. Esto también garantiza consistencia y auditabilidad.

### 4.3 Equilibrio entre acompañamiento y derivación

| Tier | Postura de la IA |
|------|-----------------|
| 1 | Acompañante empático. La derivación es un recurso, no una obligación. |
| 2 | Escucha limitada. La derivación es firme pero no urgente. Disclaimer obligatorio. |
| 3 | No acompañante. Derivación urgente. Sin LLM. Sin continuidad de conversación. |

---

## 5. Consideraciones Legales (RGPD)

### 5.1 Datos de salud mental como categoría especial

Los datos generados por el sistema de alertas —especialmente aquellos que revelan el estado de salud mental de un alumno— están clasificados como **datos de categoría especial** según el artículo 9 del Reglamento General de Protección de Datos (RGPD, Reglamento UE 2016/679). Esto implica un nivel de protección superior al aplicable a datos personales ordinarios.

### 5.2 Base legal: consentimiento e interés vital

La base legal para el tratamiento de estos datos en el contexto de alertas de seguridad es doble:

1. **Consentimiento informado (Art. 6.1.a y Art. 9.2.a RGPD)**: El alumno debe haber consentido explícitamente al uso de sus datos en el sistema. La línea de transparencia visible en el sidebar de la interfaz es una primera aproximación a este principio, pero en producción debe complementarse con una política de privacidad explícita y un mecanismo de consentimiento activo.

2. **Interés vital (Art. 9.2.c RGPD)**: El tratamiento de datos sensibles es lícito cuando "es necesario para proteger intereses vitales del interesado o de otra persona física". En situaciones de riesgo de suicidio, este fundamento legal permite el tratamiento incluso sin consentimiento previo.

### 5.3 Transparencia: línea visible en el sidebar

La interfaz Streamlit muestra una línea de aviso en el panel lateral que informa al usuario de que el sistema puede generar alertas automáticas. Esta medida cumple con el principio de **transparencia** del RGPD (Art. 5.1.a) y con el derecho a la información del interesado (Arts. 13 y 14).

### 5.4 Próximos pasos antes de producción

- Redacción de política de privacidad específica para el módulo emocional.
- Implementación de mecanismo de consentimiento activo (checkbox + registro de timestamp).
- Evaluación de Impacto relativa a la Protección de Datos (EIPD) para el tratamiento de datos de salud mental.
- Designación de Delegado de Protección de Datos (DPD) si procede.
- Acuerdo de encargado de tratamiento con los proveedores de IA (Azure/Microsoft).

---

## 6. Limitaciones Reconocidas

El sistema, tal como está implementado en su versión 1.0, tiene las siguientes limitaciones que deben reconocerse explícitamente:

1. **Clasificación imperfecta**: El clasificador basado en LLM puede producir falsos positivos (mensajes tier 1 clasificados como tier 2) o, en casos extremos, falsos negativos (mensajes tier 3 clasificados incorrectamente). La política de "ante la duda, tier 3" minimiza los falsos negativos en los casos más críticos, pero a costa de generar alertas innecesarias.

2. **Dependencia del idioma**: El clasificador está entrenado y testeado en español. Mensajes en otros idiomas pueden clasificarse incorrectamente.

3. **Contexto limitado**: El clasificador evalúa el mensaje actual de forma relativamente independiente. No tiene acceso a todo el historial de conversación para contextualizar, lo que puede llevar a clasificaciones incorrectas en conversaciones largas.

4. **El sistema NO es un dispositivo médico**: Este asistente no está homologado como dispositivo sanitario según el Reglamento UE 2017/745 (MDR). No puede utilizarse como herramienta clínica de evaluación de riesgo.

5. **Latencia de la alerta**: La alerta se escribe en disco de forma síncrona, pero el equipo receptor debe revisar activamente el log o los archivos JSON. No existe (en v1.0) un canal de notificación en tiempo real.

6. **Datos de prueba**: En el entorno de desarrollo, las alertas contienen datos de alumnos sintéticos. En producción, estos datos serían reales y requieren tratamiento conforme al RGPD.

---

## 7. Trabajo Futuro

Las siguientes extensiones están previstas para versiones posteriores del sistema, una vez superado el prototipo de TFG:

### 7.1 Notificaciones en tiempo real

- **Integración SMTP**: Envío automático de email al servicio psicológico cuando se genera una alerta tier 3, con el informe completo adjunto en PDF.
- **Integración Twilio**: SMS urgente al personal de guardia del servicio psicológico, con link al reporte completo.
- **Llamada automática**: Si el alumno está identificado y hay número de teléfono en el expediente, llamada automática de alerta.

### 7.2 Dashboard de gestión de alertas

- Interfaz web (Streamlit o React) para que el equipo psicológico visualice alertas en tiempo real.
- Filtros por severidad, estado (pendiente/atendida/cerrada), fecha y alumno.
- Registro de acciones tomadas por cada alerta (auditoría completa).
- Métricas: número de alertas por semana, tasa de respuesta, tiempo medio de atención.

### 7.3 Integración con plataformas de comunicación institucional

- **Webhook a Slack/Teams**: Canal dedicado para el equipo psicológico que recibe un mensaje estructurado con cada alerta, permitiendo respuesta coordinada.
- **Integración con el sistema de gestión académica**: Cruzar las alertas con el expediente académico para contextualizar el riesgo (alumno con bajas notas + alerta tier 3 = prioridad máxima).

### 7.4 Mejora del clasificador

- **Fine-tuning supervisado**: Entrenar un modelo especializado con casos reales anonimizados, revisados por profesionales de salud mental, para mejorar la precisión del clasificador.
- **Modelos multilingües**: Soporte para catalán, euskera, gallego y otros idiomas del territorio español.
- **Análisis de historial**: Incorporar el contexto de mensajes previos en la clasificación para reducir falsos positivos/negativos en conversaciones largas.

### 7.5 Cumplimiento legal avanzado

- Implementación del derecho de supresión (Art. 17 RGPD): permitir al alumno solicitar la eliminación de sus alertas del sistema.
- Retención limitada de datos: política automática de eliminación de alertas después de un período definido.
- Registro de actividades de tratamiento (Art. 30 RGPD) específico para el módulo de alertas.

---

*Documento elaborado como parte de la memoria del Trabajo de Fin de Grado. Para más información sobre la arquitectura técnica general del sistema, consultar el documento `TFG_Especificacion_Tecnica_v2.docx`.*
