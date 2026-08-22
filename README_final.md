# Asistente Universitario Inteligente basado en RAG y Orquestación de Agentes con LangChain y LangGraph

**Trabajo de Fin de Grado · Sistema RAG multi-agente · LangGraph + Azure AI Search + Streamlit**

---

Sistema de asistencia universitaria basado en Retrieval-Augmented Generation (RAG) con
orquestación de agentes. Responde consultas académicas e institucionales a partir de
documentación indexada en Azure AI Search, puede consultar el expediente académico de
cada alumno en SQLite y dispone de guardrails para contenido fuera de alcance y para
situaciones de apoyo emocional con tres niveles de severidad.

El asistente adopta la persona de un psicopedagogo universitario: empático, preciso y
siempre respaldado en documentación real. Disponible 24/7, con control de acceso por
roles y trazabilidad de alertas críticas.

---

## Ficha del proyecto

| | |
|---|---|
| **Autor** | Félix Godoy Salinas (NP 148387) |
| **Titulación** | Grado en Computación e Inteligencia Artificial (GCIA) |
| **Universidad** | Universidad Alfonso X el Sabio (UAX) |
| **Tutor / Director** | Leonardo Dulcetti |
| **Curso** | 2025–2026 |
| **Convocatoria** | Extraordinaria — depósito 27 de agosto de 2026 |

> **Nota terminológica:** el corpus documental del sistema pertenece a una *Universidad
> Demo* ficticia, creada específicamente para este TFG. No debe confundirse con la
> Universidad Alfonso X el Sabio, que es la institución en la que se presenta el trabajo.
> Todos los datos de alumnos son sintéticos y no corresponden a personas reales.

---

## Características principales

- **RAG híbrido**: búsqueda vectorial + semántica sobre Azure AI Search, índice
  `university-corpus` (22 documentos `.md` en 5 categorías → 94 chunks).
- **Grafo de 5 agentes** orquestado con LangGraph:
  Router → Guardrail → Retriever → Student Data → Generator.
- **3 roles de acceso**: invitado (información pública), alumno (su propio expediente),
  administrador (todos los expedientes, rangos de hasta 20 alumnos por consulta).
- **Chat conversacional** con memoria de los últimos 6 turnos y filtrado de respuestas
  vacías para evitar contaminación del historial.
- **Consulta de expediente** desde SQLite: perfil, asignaturas, notas, becas,
  convocatorias usadas.
- **Guardrail emocional en 3 niveles** (`academic_stress`, `emotional_distress`,
  `crisis_grave`) con alerta crítica automática en tier 3.
- **Control de privacidad**: los alumnos solo acceden a su propio expediente; los
  intentos de acceso indebido son bloqueados en el agente Student Data.
- **Citación de fuentes** `[Fuente: …]` en todas las respuestas del LLM.
- **Expansión de sinónimos** universitarios (22 grupos) para mejorar el recall.
- **Renderizado de fórmulas LaTeX** normalizado para Streamlit.
- **Banner de privacidad** y log de accesos en `logs/access.log` (formato JSONL).

---

## Arquitectura

### Tres capas

| Capa | Componentes |
|------|-------------|
| **Presentación** | Streamlit (`app/`): login 3 tabs, sidebar, chat, panel de fuentes, CSS |
| **Orquestación** | LangGraph (`src/graph/`, `src/agents/`): grafo compilado con 5 nodos y edges condicionales |
| **Datos** | Azure AI Search (corpus) + SQLite (`data/database/students.db`, 50 alumnos sintéticos) |

### Flujo de un mensaje por el grafo

```
START
  └─► Router         ← clasifica intent (9 valores), extrae key_points y flags
        └─► Guardrail  ← detecta out_of_scope / tier emocional (0-3)
              ├─► Generator   (guardrail activado → respuesta predefinida, sin LLM)
              └─► Retriever   (flujo normal → búsqueda híbrida Azure AI Search)
                    ├─► Student Data  (si requiere expediente y hay user_id)
                    │         └─► Generator
                    └─► Generator
                              └─► END
```

Los diagramas Mermaid detallados se encuentran en `docs/diagrams/`:

| Archivo | Contenido |
|---------|-----------|
| `agent_graph_flow.md` | Flujo completo del grafo con edges condicionales |
| `agent_architecture.md` | Capas del sistema y dependencias entre módulos |
| `data_architecture.md` | Pipeline RAG: corpus → chunking → embedding → índice → búsqueda |

---

## Los 5 agentes

| Agente | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **Router** | `src/agents/router.py` | Clasifica el intent (9 categorías), extrae `key_points`, detecta si se necesita expediente o detalle de asignatura. Temperatura 0, máx. 300 tokens. |
| **Guardrail** | `src/agents/guardrail.py` | Si intent = `EMOTIONAL_SUPPORT`: clasifica tier 0-3. Si no: detecta `out_of_scope` o `inappropriate`. Tier 3 bypasa el LLM generador. No evalúa privacidad. |
| **Retriever** | `src/agents/retriever.py` | Genera queries optimizadas, aplica expansión de sinónimos y ejecuta búsqueda híbrida. Top-K dinámico: 10 para consultas enumerativas, 5 para el resto. |
| **Student Data** | `src/agents/student_data.py` | Consulta SQLite con control de acceso por rol (`_check_access_permission`). Soporta 1 alumno, listas explícitas y rangos (máx. 20). Activa `access_violation_attempted` si el rol no tiene permiso. |
| **Generator** | `src/agents/generator.py` | Sintetiza el State completo (corpus + expediente + historial) y genera la respuesta final con GPT-4o. Extrae citas `[Fuente: …]` de la respuesta. |

### Intents soportados por el Router

```
ACADEMIC_ORIENTATION · ADMINISTRATIVE · COURSE_INFO · REGULATIONS
PROSPECTIVE_STUDENT · SCHOLARSHIPS · EMOTIONAL_SUPPORT · OUT_OF_SCOPE · GREETING
```

---

## Stack tecnológico

| Componente | Versión |
|------------|---------|
| Python | 3.11 |
| LangChain | ≥ 0.2.0 |
| LangGraph | ≥ 0.1.0 |
| langchain-openai | ≥ 0.1.0 |
| openai (Azure SDK) | ≥ 1.30.0 |
| Azure OpenAI (LLM) | GPT-4o (`gpt-4o`), api_version `2024-10-21` |
| Azure OpenAI (embeddings) | text-embedding-3-large (dim = 3 072) |
| azure-search-documents | ≥ 11.4.0 |
| azure-core / azure-identity | ≥ 1.30.0 / ≥ 1.16.0 |
| SQLite | stdlib Python |
| Streamlit | ≥ 1.35.0 (entorno de desarrollo: 1.43.2) |
| RAGAS | ≥ 0.1.9 (evaluaciones ejecutadas con 0.1.21 y 0.2.6) |
| Pydantic | ≥ 2.0.0 |
| pandas | ≥ 2.0.0 |
| pytest | ≥ 8.0.0 |
| tiktoken | ≥ 0.7.0 |
| python-dotenv | ≥ 1.0.0 |

---

## Estructura del proyecto

```
tfg-universidad-rag/
│
├── app/                              # Interfaz Streamlit
│   ├── main.py                       # Punto de entrada (streamlit run app/main.py)
│   ├── auth.py                       # Autenticación: 3 roles, log de accesos
│   ├── components/
│   │   ├── login.py                  # Pantalla de login (3 tabs)
│   │   ├── chat.py                   # Área de chat e invocación del grafo
│   │   ├── sidebar.py                # Panel lateral (selector alumno, info sesión, logout)
│   │   ├── sources_panel.py          # Panel de fuentes citadas en la respuesta
│   │   └── privacy_dialog.py         # Banner de política de privacidad (primer acceso)
│   ├── styles/main.css               # CSS personalizado
│   └── utils/
│       ├── theme.py                  # Inyección de variables CSS en Streamlit
│       └── latex.py                  # normalize_latex(): renderizado de fórmulas
│
├── src/                              # Lógica de negocio
│   ├── agents/
│   │   ├── router.py                 # Agente Router
│   │   ├── guardrail.py              # Agente Guardrail + clasificador emocional
│   │   ├── retriever.py              # Agente Retriever
│   │   ├── student_data.py           # Agente Student Data (con control de acceso)
│   │   └── generator.py              # Agente Generator (respuesta final)
│   ├── graph/
│   │   ├── graph.py                  # Ensamblaje y compilación del grafo
│   │   ├── state.py                  # TypedDict UniversityAssistantState
│   │   └── edges.py                  # Funciones de routing condicional
│   ├── tools/
│   │   ├── azure_search.py           # Búsqueda híbrida + embedding de queries
│   │   └── sqlite_query.py           # Queries predefinidas y seguras (sin SQL dinámico)
│   ├── prompts/
│   │   ├── persona.py                # Definición de la persona del asistente
│   │   ├── router_prompt.py          # Prompt del Router
│   │   ├── guardrail_prompt.py       # Prompts de guardrail y tiers emocionales
│   │   ├── retriever_prompt.py       # Prompt de generación de queries
│   │   └── generator_prompt.py       # System prompt del Generator + formateadores
│   ├── config/
│   │   ├── settings.py               # Constantes globales (TOP_K, chunk size, paths)
│   │   └── azure_config.py           # Fábricas de clientes Azure (Search, OpenAI)
│   └── utils/
│       ├── synonyms.py               # Diccionario de sinónimos (22 grupos)
│       ├── conversation.py           # Historial conversacional (últimos 6 turnos)
│       └── critical_alert.py         # Generación de alertas críticas JSON (tier 3)
│
├── data/
│   ├── alerts/                       # Alertas críticas generadas (JSON, tier 3)
│   ├── corpus/                       # 22 documentos .md en 5 categorías
│   │   ├── normativas/               # 3 docs: reglamento académico, permanencia, evaluación
│   │   ├── planes_estudio/           # 3 docs: Informática, ADE, Derecho
│   │   ├── guias_docentes/           # 8 docs: Programación I, EDAT, BD, Redes, IA Intro,
│   │   │                             #          Matemáticas I, Cálculo, Estadística
│   │   ├── faqs/                     # 4 docs: matriculación, becas, admisión, exámenes
│   │   └── procedimientos/           # 4 docs: orientación académica, apoyo riesgo,
│   │                                 #          servicios, calendario
│   └── database/
│       └── students.db               # SQLite: 50 alumnos sintéticos
│           (students_backup_20260602.db — copia de seguridad)
│
├── scripts/                          # Utilidades y mantenimiento
│   ├── generate_students.py          # Genera students.db con 50 alumnos
│   ├── create_index.py               # Crea el índice en Azure AI Search
│   ├── index_documents.py            # Fragmenta e indexa el corpus (chunks 512 tokens)
│   ├── diag_azure_connection.py      # Diagnóstico de conectividad Azure (solo lectura)
│   ├── healthcheck_smoke.py          # Smoke test del sistema completo
│   ├── verify_phase1.py              # Verifica Fase 1 (estructura y BD)
│   ├── test_retrieval.py             # Prueba de recuperación contra Azure AI Search
│   ├── test_graph_cli.py             # Prueba del grafo completo desde CLI
│   ├── diagnose_flow.py              # Diagnóstico de flujo del grafo
│   ├── view_alerts.py                # Visualiza alertas críticas generadas
│   ├── migrate_add_subject_attempts.py  # Migración: tabla de convocatorias
│   ├── migrate_add_student_grades.py    # Migración: tabla de notas
│   ├── seed_subject_attempts.py         # Poblar convocatorias
│   ├── seed_full_academic_profile.py    # Poblar perfil académico completo
│   ├── generate_eval_dataset.py         # Genera 30 muestras RAGAS
│   ├── run_ragas_eval.py                # Ejecuta evaluación RAGAS
│   └── session_summary.py               # Genera docs/Resumen_Fase5.md
│
├── tests/                            # Suite de tests
│   ├── test_tools.py                 # 26 tests: SQLite (23 unit) + Azure Search (3 integ.)
│   ├── test_agents.py                # 32 tests estructurales de los 5 agentes
│   ├── test_guardrails.py            # Tests de guardrail out-of-scope
│   ├── test_emotional_tiers.py       # Tests del clasificador de tiers emocionales
│   ├── test_auth.py                  # Tests del sistema de autenticación
│   ├── test_conversation_memory.py   # Tests de memoria conversacional
│   ├── test_enumerative.py           # Tests de consultas enumerativas
│   ├── test_grades.py                # Tests de consulta de notas
│   ├── test_synonyms.py              # Tests de expansión de sinónimos
│   ├── test_role_isolation.py        # Tests de aislamiento por roles
│   ├── test_subject_attempts.py      # Tests de convocatorias
│   ├── test_multi_student_query.py   # Tests de consultas multi-alumno (admin)
│   ├── test_flow_debug.py            # Tests de diagnóstico de flujo
│   ├── test_history_fix.py           # Tests de corrección de historial
│   ├── test_integration.py           # Tests de integración end-to-end
│   ├── conftest.py                   # Fixtures compartidas
│   ├── test_cases.json               # 30 casos parametrizados (intent + guardrail)
│   ├── eval_dataset.json             # Dataset RAGAS: 30 muestras curadas
│   ├── eval_dataset_meta.json        # Metadatos del dataset (intent, chunks, confidence)
│   ├── ragas_report.json             # Scores RAGAS v1 por muestra
│   ├── ragas_report_v2.json          # Scores RAGAS v2 por muestra
│   ├── ragas_summary.txt             # Tabla resumen v1
│   └── ragas_summary_v2.txt          # Tabla comparativa v1 vs v2
│
├── docs/
│   ├── diagrams/
│   │   ├── agent_graph_flow.md       # Diagrama Mermaid del flujo del grafo
│   │   ├── agent_architecture.md     # Diagrama de capas y dependencias
│   │   └── data_architecture.md      # Pipeline RAG
│   ├── EMOTIONAL_GUARDRAIL_DESIGN.md # Diseño del sistema emocional en 3 tiers (RGPD, ética)
│   ├── AUTH_DESIGN.md                # Diseño del control de acceso y sus limitaciones
│   ├── PENDIENTES_REVISION.md        # Hallazgos y limitaciones detectadas en Fase 4-5
│   ├── Resumen_Fase5.md              # Resumen de resultados de Fase 5 (generado automáticamente)
│   ├── Reevaluacion_RAGAS.md         # Re-evaluación con RAGAS 0.2.6 y dataset corregido
│   ├── Informe_Verificacion_Sistema.docx
│   ├── Memoria_TFG_Entrega1.docx
│   └── Memoria_TFG_Entrega2.docx
│
├── logs/                             # Logs de ejecución por fase y fecha
├── backups/                          # Snapshots de la UI en distintas iteraciones
├── requirements.txt
├── .env.example                      # Plantilla de variables de entorno (sin secretos)
├── .gitignore
├── CLAUDE.md                         # Instrucciones para Claude Code
└── README.md                         # Este documento
```

> **Nota sobre el recuento del corpus:** el archivo `docs/Resumen_Fase5.md` (generado el
> 2026-06-04) reporta 19 documentos, y el diagrama `data_architecture` arrastra esa misma
> cifra. El recuento real de archivos `.md` en `data/corpus/` es **22**, que producen
> **94 chunks** en el índice. La discrepancia se debe a que varias guías docentes se
> añadieron después de generarse aquel resumen. La cifra correcta es 22.

---

## Esquema de la base de datos (`students.db`)

| Tabla | Contenido |
|-------|-----------|
| `students` | Perfil: `id`, `name`, `email`, `degree`, `year`, `gpa`, `credits_completed`, `credits_total`, `status`, `enrolled_year` |
| `subject_records` | Asignaturas por alumno: `subject_code`, `subject_name`, `credits`, `grade`, `semester`, `status` |
| `scholarships` | Becas: `type`, `amount`, `year`, `status` |
| `student_subject_attempts` | Convocatorias: `subject_code`, `attempts_used`, `attempts_max`, `last_attempt_year`, `status` |
| `student_grades` | Histórico de notas: `subject_code`, `attempt_number`, `academic_year`, `grade`, `passed` |

La BD contiene **50 alumnos sintéticos** generados con `scripts/generate_students.py`.
El LLM nunca escribe SQL directamente: el agente Student Data llama a funciones
predefinidas y parametrizadas en `src/tools/sqlite_query.py` (decisión de diseño
deliberada, sin Text-to-SQL, por seguridad y predictibilidad).

**Alumnos representativos para pruebas:**

| ID | Nombre | Grado | Perfil |
|----|--------|-------|--------|
| ALU001 | Carlos Vega Cruz | Informática 4º | GPA 9.1, `excellent` |
| ALU015 | Sergio Delgado Peña | Informática 2º | GPA 4.2, `at_risk` |
| ALU017 | Manuel Martínez Cano | Informática 2º | GPA 8.33, `active` |
| ALU030 | Isabel Blanco Pérez | ADE 3º | GPA 7.8, `active`, beca MEC |

---

## Requisitos previos

- **Python 3.11**.
- **Cuenta Azure** con recursos activos:
  - Azure OpenAI Service — despliegues `gpt-4o` y `text-embedding-3-large`.
  - Azure AI Search — índice `university-corpus` (tier Basic o superior si se desea
    ranker semántico; el tier Free no lo incluye).
- Git.

### Variables de entorno (`.env.example`)

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint del servicio Azure OpenAI | — |
| `AZURE_OPENAI_API_KEY` | Clave de API de Azure OpenAI | — |
| `AZURE_OPENAI_API_VERSION` | Versión de la API | `2024-10-21` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Despliegue del modelo de chat | `gpt-4o` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Despliegue de embeddings | `text-embedding-3-large` |
| `AZURE_SEARCH_SERVICE_ENDPOINT` | Endpoint del servicio de búsqueda | — |
| `AZURE_SEARCH_API_KEY` | Clave de API de Azure AI Search | — |
| `AZURE_SEARCH_INDEX_NAME` | Nombre del índice | `university-corpus` |
| `SQLITE_DB_PATH` | Ruta a la BD SQLite | `data/database/students.db` |
| `STUDENT_PASSWORD` | Contraseña común de alumnos | — |
| `ADMIN_PASSWORD` | Contraseña de administrador | — |
| `MAX_RETRIEVED_DOCS` | Máximo de documentos recuperados | `5` |
| `RETRIEVAL_SCORE_THRESHOLD` | Umbral de relevancia mínima | `0.7` |
| `USE_SQLITE_CHECKPOINTER` | `false` = MemorySaver, `true` = SqliteSaver | `false` |
| `DEBUG_MODE` | Activa logging verbose | `false` |

> **Importante:** el archivo `.env` está excluido del repositorio por `.gitignore` y
> nunca ha sido versionado. Nunca subir credenciales reales al repositorio. Se
> recomienda usar una *query key* de solo lectura para `AZURE_SEARCH_API_KEY` en lugar
> de la clave de administración.

---

## Instalación y configuración

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd tfg-universidad-rag

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales Azure y contraseñas del sistema
```

---

## Puesta en marcha

### Paso 1 — Generar la base de datos de alumnos

```bash
python scripts/generate_students.py
```

Crea `data/database/students.db` con 50 alumnos sintéticos y todas las tablas
necesarias (incluidas las migraciones de convocatorias y notas).

### Paso 2 — Crear el índice en Azure AI Search

```bash
python scripts/create_index.py
```

Crea el índice `university-corpus` con campos de búsqueda híbrida (vectorial + semántica)
y configuración semántica `semantic-config`.

### Paso 3 — Indexar el corpus

```bash
python scripts/index_documents.py
```

Fragmenta los 22 documentos en chunks de 512 tokens con solapamiento de 50 (tokenizador
`cl100k_base`), genera embeddings con `text-embedding-3-large` (dim = 3 072) y los sube
al índice de Azure. Resultado esperado: 94 chunks.

### Paso 4 — Verificar el sistema

```bash
python scripts/diag_azure_connection.py   # Conectividad Azure (Search + OpenAI)
python scripts/healthcheck_smoke.py       # Smoke test del sistema completo
```

Comprueban: grafo LangGraph compilado correctamente, SQLite operativo (ALU001 accesible),
cliente Azure Search configurado, búsqueda semántica y no semántica funcionales.

### Paso 5 — Lanzar la interfaz

```bash
streamlit run app/main.py
```

Abre en el navegador en `http://localhost:8501` (puerto por defecto de Streamlit).

> **Nota sobre el estado de la infraestructura:** el recurso de Azure AI Search se
> eliminó tras la fase de demostración, ya que el tier Basic factura por tiempo de
> existencia del servicio y no ofrece opción de pausa. El recurso de Azure OpenAI se
> conservó (no genera coste en reposo). Para volver a ejecutar el sistema completo basta
> con recrear el servicio de búsqueda y repetir los pasos 2 y 3; el corpus y el código
> permanecen intactos en el repositorio.

---

## Uso

### Modos de acceso

| Rol | Cómo acceder | Capacidades |
|-----|-------------|-------------|
| **Invitado** | Tab "Invitado" → botón "Continuar como invitado" | Información pública: normativas, planes de estudio, FAQs, becas, procedimientos |
| **Alumno** | Tab "Alumno" → seleccionar ID + contraseña | Información pública + expediente propio (notas, convocatorias, créditos, becas) |
| **Admin** | Tab "Admin" → contraseña | Acceso completo: selector de alumno en sidebar, consultas de rangos de alumnos |

### Ejemplos de consultas

**Información pública (cualquier rol):**
- "¿Cuántas convocatorias tiene un alumno para superar una asignatura?"
- "¿Cómo funciona el procedimiento de beca de colaboración?"
- "¿Cuáles son los requisitos de admisión para el Grado en Informática?"
- "¿Cuándo es el período de matrícula?"

**Con expediente (alumno autenticado):**
- "¿Cuántos créditos me quedan para terminar la carrera?"
- "¿Cuál es mi nota media?"
- "¿Qué asignaturas tengo pendientes?"
- "¿Cuántas veces he intentado Programación I?"
- "¿Tengo alguna beca activa?"

**Administrador:**
- "Dame los expedientes de ALU001 al ALU005"
- "¿Cuál es el estado académico de ALU015?"
- "Compara el rendimiento de ALU001 y ALU015"

---

## Evaluación y pruebas

### Ejecutar la suite de tests

```bash
# Suite completa (requiere Azure activo para tests de integración)
pytest tests/

# Solo tests unitarios de SQLite (sin Azure)
pytest tests/test_tools.py -k "not integration"

# Con output detallado
pytest tests/ -v
```

### Resultados (Fase 5, 2026-06-04)

| Suite | Tests | Pasados | Fallidos |
|-------|-------|---------|----------|
| SQLite unit tests (`test_tools.py`) | 23 | 23 | 0 |
| Azure Search integration (`test_tools.py`) | 3 | 3 | 0 |
| Agent structural tests (`test_agents.py`) | 32 | 32 | 0 |
| **TOTAL** | **58** | **58** | **0** |

### Evaluación RAGAS

El dataset de evaluación (`tests/eval_dataset.json`) contiene 30 muestras curadas que
cubren todos los intents RAG (normativas, planes de estudio, guías docentes, FAQs,
procedimientos). Se han ejecutado dos evaluaciones con distintas versiones de RAGAS:

| Métrica | v1 (RAGAS 0.1.21) | v2 (RAGAS 0.2.6) | Objetivo TFG | Cumple |
|---------|--------------------|-------------------|--------------|--------|
| `faithfulness` | 0.5118 | 0.5521 | ≥ 0.85 | No |
| `answer_relevancy` | 0.4755 | 0.5104 | ≥ 0.80 | No |
| `context_precision` | 0.3756 | 0.2956 | ≥ 0.75 | No |
| `context_recall` | 0.2730 | 0.3111 | ≥ 0.70 | No |

Ninguna métrica alcanza el objetivo establecido. La re-evaluación v2 corrigió un
artefacto de medición real (el `column_map` de RAGAS 0.2.x, que sin mapear devolvía
nulos contabilizados como 0 y hundía las medias), actualizó la librería y corrigió cinco
`ground_truths` con errores factuales respecto al corpus. Las mejoras resultantes son
modestas: el sistema, bien medido, no alcanza los umbrales. El descenso de
`context_precision` responde a una metodología más estricta en 0.2.x, no a un empeoramiento.

**Interpretación (documentada en la memoria):** las métricas se leen en triangulación con
la evaluación manual y los tests unitarios. Tres factores explican la brecha entre las
cifras y el comportamiento observado: (a) el sistema penaliza su propia honestidad al
responder "no dispongo de ese dato" en lugar de inventar; (b) recuperar 5 fragmentos
amplios prioriza cobertura sobre precisión; (c) la cobertura del corpus en guías docentes
es parcial (8 guías).

> **Criterio de integridad académica:** las métricas se reportan tal como fueron medidas,
> sin maquillaje. Están ligadas al backend original (Azure AI Search + GPT-4o) y no se
> recalculan sobre ningún sistema alternativo.

### Evaluación manual dirigida

12 consultas ejecutadas en conversaciones limpias sobre los tres roles (alumno, invitado,
administrador). Resultado: 10 de 12 correctas o excelentes. Las dos restantes eran
consultas agregadas globales, fuera del alcance de diseño del sistema (ver limitaciones).

**Para ejecutar la evaluación:**

```bash
python scripts/generate_eval_dataset.py   # Genera tests/eval_dataset.json (≈6 min)
python scripts/run_ragas_eval.py          # Genera tests/ragas_report.json y ragas_summary.txt
```

---

## Sistema de guardrail emocional

El guardrail clasifica los mensajes con intent `EMOTIONAL_SUPPORT` en 4 niveles:

| Tier | Etiqueta | Comportamiento |
|------|----------|----------------|
| 0 | (ninguno) | Flujo normal |
| 1 | `academic_stress` | Respuesta empática + mención del servicio psicológico como recurso |
| 2 | `emotional_distress` | Respuesta empática + disclaimer obligatorio (IA ≠ profesional) + derivación |
| 3 | `crisis_grave` | Respuesta predefinida con recursos de emergencia (Psicología, 024, 112). NO pasa por el LLM. Genera alerta crítica automática en `data/alerts/*.json` y `logs/critical_alerts.log`. Nunca invita a continuar la conversación con la IA |

La política de clasificación es conservadora: ante ambigüedad entre tier 2 y tier 3, el
sistema clasifica siempre como tier 3 (sesgo deliberado al alza, prefiriendo falsos
positivos a falsos negativos).

Ver diseño completo, consideraciones éticas y RGPD en `docs/EMOTIONAL_GUARDRAIL_DESIGN.md`.

---

## Control de privacidad

La protección del expediente académico se articula en dos capas efectivas más una de
trazabilidad:

1. **Filtrado SQL por identificador** (capa primaria): `_check_access_permission()` en
   `src/agents/student_data.py` verifica el rol y el `user_id` autenticado antes de
   ejecutar cualquier consulta. Un alumno solo puede consultar su propio expediente.
2. **Prompt del Generator** (capa secundaria): reglas de privacidad por rol en el system
   prompt, que impiden revelar datos que no estén legítimamente en el State.
3. **Trazabilidad**: el intento no autorizado marca el flag `access_violation_attempted`
   y emite una advertencia por consola (`logger.warning`). El fichero `logs/access.log`
   registra únicamente los inicios de sesión.

---

## Estado del proyecto

| Fase | Descripción | Estado | Log representativo |
|------|-------------|--------|--------------------|
| **Fase 1** | Cimientos: corpus sintético, SQLite, estructura del proyecto | ✅ Completada | `logs/fase1_20260423.txt` |
| **Fase 2** | Azure AI Search: creación del índice e indexación del corpus | ✅ Completada | `logs/fase2_20260513.txt` |
| **Fase 3A** | Router, Guardrail, State, Graph — estructura del grafo | ✅ Completada | `logs/fase3a_20260513.txt` |
| **Fase 3B** | Integración completa: Student Data, Generator, tiers emocionales, autenticación | ✅ Completada | `logs/fase3b_20260602.txt` |
| **Fase 4** | Interfaz Streamlit con 3 roles, CSS, privacidad, refinamientos UI v1/v2/v3 | ✅ Completada | `logs/fase4_20260527.txt` |
| **Fase 5** | Tests (58/58 ✓), evaluación RAGAS, re-evaluación v2, cierre y documentación | ✅ Completada | `logs/fase5_20260604.txt` |
| **Cierre** | Correcciones finales, grabación de la demo y respaldo del repositorio | ✅ Completada | agosto 2026 |

### Correcciones aplicadas en la fase de cierre (agosto 2026)

Rama `fase-5-bis`:

| Fix | Descripción | Commit |
|-----|-------------|--------|
| **Renderizado LaTeX** | Nuevo `app/utils/latex.py` con `normalize_latex()`: convierte `\[…\]` → `$$…$$` y `\(…\)` → `$…$` para que Streamlit renderice las fórmulas correctamente. Cableado en `chat.py` solo para mensajes del asistente | `3761558` |
| **Falsos subíndices** | `normalize_latex()` deja de interpretar identificadores en snake_case (`at_risk`, `student_id`) como subíndices LaTeX; solo procesa `_{…}` / `^{…}` con llaves y comandos LaTeX reales | `e1d8673` |
| **Detalle de asignaturas pendientes (F3)** | Se añadió "pendiente" y variantes al detector de keywords, y se amplió `format_student_context` para pasar al Generator **todas** las asignaturas pendientes con código y créditos, en lugar de truncar a tres nombres | `fix(f3)…` |

Estas correcciones afectan a la capa de presentación y al formateo del contexto; son
independientes del dataset documental de RAGAS, por lo que las métricas no se recalcularon.

### Limitaciones conocidas

1. **Métricas RAGAS por debajo del objetivo.** El generador sintetiza información de
   múltiples chunks en lugar de reproducirlos literalmente, lo que penaliza
   `faithfulness` en la medición. Las respuestas son semánticamente correctas. Detalle y
   propuestas de mejora en `docs/Reevaluacion_RAGAS.md`.

2. **Consultas agregadas no soportadas (F1/F2).** Todas las funciones de
   `sqlite_query.py` operan sobre un `student_id` individual; no existen funciones de
   `COUNT`/`AVG`/`GROUP BY`. Es consecuencia directa de la decisión de no usar
   Text-to-SQL. Ante preguntas como "¿cuántos alumnos hay en riesgo?", el sistema
   responde honestamente que no puede acceder al listado global en lugar de inventar una
   cifra. Límite de alcance, no error.

3. **Frontera COURSE_INFO / ADMINISTRATIVE (caso UI02).** El Router clasifica como
   `ADMINISTRATIVE` algunas consultas que combinan matrícula y contenido de asignatura
   (p. ej. "¿Qué necesito para matricularme en IA?"). Impacto bajo: el RAG mitiga el
   efecto y la respuesta sigue siendo útil y fundamentada. Documentado en
   `docs/PENDIENTES_REVISION.md`.

4. **Autenticación simplificada para demo.** Contraseña compartida entre alumnos, en
   texto plano en `.env`, sin hash, sin expiración de sesión ni rate limiting. Apropiado
   para un prototipo académico; no apto para producción. Camino hacia producción
   (bcrypt + BD de usuarios + credenciales individuales) descrito en `docs/AUTH_DESIGN.md`.

5. **Alertas de tier 3 solo en disco.** Las alertas de crisis grave se escriben en
   `data/alerts/*.json` y `logs/critical_alerts.log`. No existe canal de notificación en
   tiempo real (email, SMS, webhook). Canales previstos para producción documentados en
   `docs/EMOTIONAL_GUARDRAIL_DESIGN.md`.

6. **Violaciones de privacidad no persistidas.** Los intentos de acceso indebido se
   bloquean y se emiten por consola, pero no se escriben en un fichero de auditoría
   dedicado. Decisión consciente: la protección efectiva la ejerce el filtrado que impide
   el acceso, no el registro posterior.

---

## Licencia y autoría

**Autor:** Félix Godoy Salinas (NP 148387)
**Contexto:** Trabajo de Fin de Grado — Grado en Computación e Inteligencia Artificial,
Universidad Alfonso X el Sabio (UAX)
**Tutor:** Leonardo Dulcetti
**Curso:** 2025–2026

No se ha definido licencia explícita en el repositorio. El corpus documental corresponde
a una universidad ficticia creada para este trabajo y los datos de alumnos son sintéticos:
no corresponden a personas ni a instituciones reales.

---

*Última actualización: agosto de 2026.*
