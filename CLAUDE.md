# CLAUDE.md — Instrucciones para Claude Code

## Descripción del proyecto

Sistema RAG multi-agente para orientación universitaria. Usa LangGraph para orquestar 5 agentes especializados, Azure AI Search para recuperar documentación institucional y SQLite para consultar expedientes académicos. Interfaz web con Streamlit.

Documentos de referencia en `E:\TFG\Info\`:
- `TFG_Especificacion_Tecnica_v2.docx` — Especificación completa (fuente de verdad)
- `TFG_Fases_Desarrollo.txt` — Plan de fases de desarrollo
- `TFG_Prompt_Fase1.txt` — Instrucciones detalladas de Fase 1

## Los 5 agentes y sus archivos

| Agente | Archivo | Input → Output |
|--------|---------|----------------|
| Router | `src/agents/router.py` | user_message → intent, key_points, requires_student_data |
| Guardrail | `src/agents/guardrail.py` | intent, key_points → guardrail_triggered, guardrail_reason |
| Retriever | `src/agents/retriever.py` | key_points, intent → retrieved_docs, search_queries |
| Student Data | `src/agents/student_data.py` | user_id → student_record |
| Generador | `src/agents/generator.py` | State completo → final_response, sources, confidence |

## Orden de desarrollo (Sección 14.2 del doc)

1. Crear estructura de directorios completa (hecho)
2. Crear `.env.example`, `.gitignore`, `requirements.txt` y `README.md` (hecho)
3. Implementar `src/graph/state.py` con el TypedDict del State
4. Implementar `src/config/` con la configuración de Azure
5. Implementar `src/tools/azure_search.py` y `src/tools/sqlite_query.py`
6. Implementar `src/prompts/persona.py` y los prompts de cada agente
7. Implementar cada agente en `src/agents/` (router → guardrail → retriever → student_data → generator)
8. Implementar `src/graph/edges.py` con las funciones de decisión condicional
9. Implementar `src/graph/graph.py` ensamblando el grafo completo
10. Implementar `app/` con la interfaz Streamlit
11. Crear `scripts/generate_students.py` y ejecutarlo para poblar SQLite
12. Crear `scripts/index_documents.py` para indexar el corpus en Azure AI Search
13. Crear el corpus documental en `data/corpus/`
14. Implementar `tests/`

## Convenciones de código (Sección 14.3)

- **Tipado**: Type hints completos en todas las funciones y clases
- **Docstrings**: Formato Google style en todas las funciones y clases
- **Logging**: Usar el módulo `logging`, nunca `print()`. DEBUG para el grafo, INFO para las tools
- **Errores**: Todas las llamadas a APIs externas (Azure) deben tener `try/except` con mensajes descriptivos
- **Variables de entorno**: Siempre `os.getenv()` o `python-dotenv`. Nunca hardcodear claves

## Comandos más usados

```bash
# Ejecutar la aplicación
streamlit run app/main.py

# Ejecutar todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_agents.py -v
pytest tests/test_guardrails.py -v

# Generar base de datos de alumnos
python scripts/generate_students.py

# Indexar corpus en Azure (requiere .env con credenciales)
python scripts/index_documents.py

# Verificar estado de Fase 1
python scripts/verify_phase1.py

# Ver logs recientes
ls logs/
```

## Reglas importantes

- Si un test falla, mostrar el error, diagnóstico y propuesta de solución antes de aplicarla
- El archivo `.env` NUNCA debe crearse con claves reales. Solo `.env.example`
- Los logs se guardan en `logs/` con timestamp: `logs/fase1_YYYYMMDD.txt`
- No avanzar a la siguiente fase sin que verify_phase1.py pase todos los checks
- La Fase 2 requiere que Felix proporcione las credenciales Azure en `.env`
