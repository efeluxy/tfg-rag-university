# Pendientes de revisión — Detectados en cierre de Fase 4

**Fecha de detección:** 27 mayo 2026
**Estado de Fase 4:** SUPERADA (no bloquean Fase 5)
**Tratamiento sugerido:** documentar en memoria + abordar en Fase 5 si hay margen

---

## 1. [PRIORITARIO] Fallo de clasificación en UI02 — Frontera COURSE_INFO / ADMINISTRATIVE

**Caso de test:** `UI02 — Consulta requisitos asignatura`
**Mensaje:** *"Que necesito para matricularme en la asignatura de IA?"*
**Intent esperado:** `COURSE_INFO`
**Intent obtenido:** `ADMINISTRATIVE`

**Diagnóstico:**
La frontera entre los intents `COURSE_INFO` (información de asignatura) y `ADMINISTRATIVE` (trámites)
es genuinamente ambigua cuando la consulta combina ambos conceptos ("requisitos de matriculación
en una asignatura específica"). El Router toma una decisión defendible pero no coincide con el
intent etiquetado en el caso de test.

**Impacto:**
Bajo. El sistema sigue funcionando: el retriever buscará en chunks de categoría administrativa
y devolverá una respuesta útil. No produce respuestas inseguras ni alucinaciones.

**Acción correctora — opciones:**
- Opción A (rápida): refinar el prompt del Router con ejemplos few-shot que distingan estos dos
  casos frontera. Añadir 2-3 ejemplos en `src/prompts/router_prompt.py`.
- Opción B (profunda): rediseñar la taxonomía de intents para que sean mutuamente excluyentes,
  o introducir un intent híbrido tipo `COURSE_ENROLLMENT`.
- Opción C (académica): documentar como limitación conocida en la memoria. Honestidad técnica.

**Recomendación:** combinación de A + C. Aplicar few-shot en Fase 5 si queda margen, y
documentar la decisión en el capítulo de resultados.

---

## 2. Respuesta sin fuentes citadas en consultas con expediente

**Caso de test:** Caso 2 del Test 2 de Fase 4 (ALU001, consulta de orientación)
**Síntoma:** `Sources: []` en la respuesta final, pese a que el flujo del grafo pasa por Retriever.

**Diagnóstico (a confirmar en Fase 5):**
Tres hipótesis posibles:
1. El retriever no encontró chunks con score suficiente para esta consulta concreta.
2. El Generator priorizó los datos del expediente (Student Data) sobre el corpus indexado y
   no incluyó las citas del retriever.
3. Las fuentes se filtraron en el postprocesado del Generator.

**Cómo lo mediremos:**
RAGAS evaluará `context_recall` (¿qué fracción del contenido necesario está en los chunks
recuperados?) y `context_precision` (¿son los chunks recuperados realmente relevantes?). Si
ambas métricas salen altas pero las sources finales aparecen vacías, el problema está en el
Generator. Si salen bajas, el problema está aguas arriba en el Retriever o en el corpus.

**Acción correctora:** depende del diagnóstico. No se toca hasta tener los números de Fase 5.

---

## 3. [MENOR] LOG_PATH hardcoded en tests

**Archivos afectados:**
- `tests/test_guardrails.py` línea ~14: `LOG_PATH = ... / "test_guardrails_20260527.txt"`
- `tests/test_integration.py` línea ~14: `LOG_PATH = ... / "test_integration_20260527.txt"`

**Problema:**
Si los tests se relanzan otro día, el log se sobreescribe en lugar de generar uno nuevo con la
fecha de ejecución.

**Acción correctora (1 minuto):**
```python
from datetime import date
LOG_PATH = Path(__file__).parent.parent / "logs" / f"test_guardrails_{date.today():%Y%m%d}.txt"
```

**Cuándo:** al tocar estos archivos en Fase 5 (Bloque 5.3 amplía la suite de tests). No urge.

---

---

## Actualización tras mejoras de Fase 5 (2026-06-02)

### Punto #1 (UI02) — Estado: SIN RESOLVER (previsto)
El intent UI02 sigue clasificándose como ADMINISTRATIVE en lugar de COURSE_INFO.
La introducción de `requires_subject_detail` no cambia el resultado en este caso
concreto porque el mensaje ("matricularme en la asignatura de IA") no menciona
código de asignatura. El flag funciona correctamente para consultas con código
explícito (ej. INF201). Documentar como limitación conocida.

### Punto #2 (Sources vacío) — Estado: PARCIALMENTE RESUELTO
El top_k dinámico (10 docs para consultas enumerativas vs 5 para el resto) mejora
la cobertura del retriever. Las consultas con expediente ahora incluyen además las
convocatorias como contexto adicional, lo que reduce el riesgo de respuestas sin
fuentes. Seguimiento completo pendiente de métricas RAGAS.

### Punto #3 (LOG_PATH hardcoded) — Estado: RESUELTO
Los nuevos tests (test_subject_attempts, test_conversation_memory, test_enumerative)
usan `date.today()` para generar el LOG_PATH dinámicamente.

---

## Resumen para tribunal / memoria

De los tres puntos, el **#1 es el que merece dos párrafos en la sección de limitaciones** de la
memoria. Los otros dos son detalles de implementación que no aportan al discurso académico.

---

## Refinamientos UI (2026-06-02)

Aplicados via TFG_Prompt_UI_Refinements.txt. Notas:

- El sticky de la sidebar depende del flexbox que Streamlit aplica al
  contenedor padre. Si una version futura de Streamlit cambia esa
  estructura, revisar los selectores `section[data-testid="stSidebar"]`
  y `[data-testid="stColumn"]:first-child` (la app usa columnas, no sidebar nativa).
- El selector :has() requiere navegadores modernos (Chrome 105+, Firefox
  121+, Safari 15.4+). Verificado en local. Trabajo futuro: fallback con
  JavaScript para navegadores antiguos.
- El toggle de tema NO persiste entre sesiones del navegador (no se usa
  localStorage). Trabajo futuro: persistencia con st.experimental_user
  o cookies firmadas.
- La politica de privacidad en privacy_dialog.py es texto estatico. En
  produccion deberia centralizarse en un documento legal versionado.
