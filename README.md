# Asistente Universitario Inteligente

Sistema de asistencia universitaria basado en Retrieval-Augmented Generation (RAG) con arquitectura multi-agente. El sistema combina Azure AI Search para la recuperación de documentación institucional, una base de datos SQLite con expedientes académicos de alumnos, y un grafo de agentes LangGraph orquestado que genera respuestas personalizadas.

El asistente adopta la persona de un psicopedagogo universitario: empático, preciso y siempre referenciado en documentación real. Atiende consultas de alumnos matriculados (con acceso a su expediente) y de futuros alumnos (información pública), disponible 24/7 y con guardrails integrados para derivar a profesionales humanos cuando es necesario.

## Arquitectura — Los 5 agentes

| Agente | Archivo | Rol |
|--------|---------|-----|
| Router | `src/agents/router.py` | Clasifica el intent y extrae puntos clave del mensaje |
| Guardrail | `src/agents/guardrail.py` | Detecta contenido fuera de alcance, inapropiado o crisis emocional |
| Retriever | `src/agents/retriever.py` | Busca chunks relevantes en Azure AI Search (búsqueda híbrida) |
| Student Data | `src/agents/student_data.py` | Consulta el expediente del alumno en SQLite |
| Generador | `src/agents/generator.py` | Sintetiza todo el contexto y genera la respuesta final con fuentes |

## Requisitos del sistema

- Python 3.11+
- Cuenta Azure con los siguientes recursos activos:
  - Azure OpenAI Service (despliegue GPT-4o + text-embedding-3-large)
  - Azure AI Search (índice `university-corpus`)
- Git

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd tfg-universidad-rag

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales Azure reales

# 5. Generar base de datos de alumnos
python scripts/generate_students.py

# 6. Indexar el corpus en Azure AI Search (requiere credenciales)
python scripts/index_documents.py
```

## Cómo ejecutar

```bash
# Iniciar la interfaz web
streamlit run app/main.py

# Ejecutar tests
pytest tests/

# Verificar estado de la Fase 1
python scripts/verify_phase1.py
```

## Estructura de carpetas

```
tfg-universidad-rag/
├── app/                    # Interfaz Streamlit
│   ├── main.py
│   └── components/
├── src/                    # Lógica de negocio
│   ├── agents/             # Los 5 agentes LangGraph
│   ├── graph/              # Estado y orquestación
│   ├── tools/              # Azure Search + SQLite
│   ├── prompts/            # System prompts de cada agente
│   └── config/             # Configuración y clientes Azure
├── data/
│   ├── corpus/             # Documentación universitaria sintética
│   └── database/           # SQLite con expedientes de alumnos
├── scripts/                # Scripts de utilidad
├── tests/                  # Tests funcionales
├── logs/                   # Logs de ejecución
└── docs/diagrams/          # Diagramas Mermaid para la memoria
```

## Estado del desarrollo

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Cimientos y datos sintéticos (sin Azure) | ✅ Completada |
| Fase 2 | Azure AI Search e indexación | ⏳ Pendiente (requiere credenciales) |
| Fase 3 | LangGraph — Agentes y grafo | ⏳ Pendiente |
| Fase 4 | Interfaz Streamlit | ⏳ Pendiente |
| Fase 5 | Tests, evaluación RAGAS y cierre | ⏳ Pendiente |

## Autor

Félix García — TFG Ingeniería Informática, Universidad Demo
