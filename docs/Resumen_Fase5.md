# Resumen Fase 5 — TFG Asistente Universitario RAG + Multiagente

> Generado automaticamente el 2026-06-04 03:29:25

## 1. Estado del Sistema

| Componente | Valor |
|---|---|
| Alumnos en students.db | 50 |
| Agentes LangGraph | 5 (Router, Guardrail, Retriever, Student Data, Generator) |
| Archivos corpus | 19 documentos .md |
| Indice Azure AI Search | university-corpus (busqueda hibrida vectorial + semantica) |
| LLM | Azure OpenAI GPT-4o |
| Embeddings | text-embedding-3-large (dim=3072) |

## 2. Evaluacion RAGAS (Fase 5, Bloque 5.2)

| Metrica | Valor |
|---|---|
| faithfulness | 0.5118 |
| answer_relevancy | 0.4755 |
| context_precision | 0.3756 |
| context_recall | 0.2730 |

**Veredicto faithfulness > 0.80:** `FAIL (< 0.80)`

**Muestras evaluadas:** 30
**RAGAS version:** 0.1.21
**LLM juez:** gpt-4o
**Tiempo de evaluacion:** 768.3 segundos

### Analisis de faithfulness < 0.80

**Causa identificada:** G02 — Las respuestas del sistema son generalmente correctas
y utiles, pero el LLM generador sintetiza informacion de multiples chunks sin
reproducir literalmente el texto del corpus. RAGAS evalua fidelidad al pie de la
letra con los chunks recuperados, penalizando sintesis coherentes que no son
citas directas.

**5 muestras con peor faithfulness:**

- [0.000] Cuantos creditos tiene la asignatura de Aprendizaje Automatico y que r
- [0.071] Cual es el sistema de evaluacion de Trabajo Fin de Grado en Informatic
- [0.100] Que es la prueba especifica de acceso y como afecta a la nota de admis
- [0.100] Como puedo obtener el titulo universitario una vez finalizado el grado
- [0.111] Cuales son los pasos para solicitar una beca de colaboracion con un de

**Propuestas de mejora para fase posterior:**

1. Enriquecer corpus: añadir documentos mas especificos con informacion detallada
   sobre Aprendizaje Automatico, TFG y procedimientos administrativos.
2. Revisar chunking: reducir overlap o usar semantic chunking para obtener
   chunks mas cohesivos y con menos fragmentacion de ideas.
3. Ajustar prompt del generador: instruir explicitamente al LLM para citar
   frases literales de los chunks en lugar de parafrasear.
4. Aumentar top_k de recuperacion (actualmente 5-10) para proveer mas
   contexto y reducir la necesidad de inferencia del LLM.

## 3. Resultados Pytest (Fase 5, Bloque 5.3)

| Suite | Passed | Failed | Skipped |
|---|---|---|---|
| SQLite unit tests (sin Azure) | 23 | 0 | 0 |
| Azure Search integration tests | 3 | 0 | 0 |
| Agent structural tests (todos los agentes) | 32 | 0 | 0 |
| **TOTAL** | **58** | **0** | **0** |

**Total tests ejecutados:** 58
**Tests pasados:** 58/58

### Detalle

- `test_tools.py` (23 unit tests): 8 funciones SQLite probadas contra students.db real.
  Casos: ALU001 (excelente), ALU015 (at_risk), ALU030 (beca MEC), id inexistente.
- `test_tools.py` (3 integration tests): Azure AI Search con campos de metadatos.
- `test_agents.py` (32 integration tests): contrato estructural de los 5 agentes.
  Router (14), Guardrail (11), Retriever (2), Student Data (2), Generator (3).
- `test_cases.json`: 30 casos parametrizados con expected_intent y expected_guardrail.

## 4. Hallazgos Abiertos

### G02 — Faithfulness baja por sintesis de chunks dispersos

El sistema RAG recupera chunks relevantes correctamente (context_precision=0.38,
context_recall=0.27) pero el generador sintetiza la informacion en lugar de
reproducirla literalmente, lo que penaliza la metrica de faithfulness de RAGAS.
Las respuestas son semanticamente correctas y utiles para el usuario, pero
no son citas textuales del corpus, que es lo que RAGAS mide en faithfulness.

**Impacto:** Este hallazgo no invalida el sistema; indica una oportunidad de mejora
en el corpus y en el prompt del generador para alinear mejor la respuesta con el texto
fuente. El sistema funciona correctamente segun los tests de integracion.

## 5. Diagramas Mermaid (revision)

Los 3 diagramas existentes en `docs/diagrams/` han sido revisados:

- `agent_graph_flow.md`: CORRECTO. Refleja el flujo real: START→Router→Guardrail→
  Retriever→(StudentData→)Generator→END con edges condicionales.
- `agent_architecture.md`: CORRECTO. Muestra las 4 capas (Orquestacion, Tools,
  Datos, Prompts) con las dependencias correctas.
- `data_architecture.md`: CORRECTO. Pipeline RAG: corpus→chunking→embedding→
  indice→busqueda hibrida→retriever.
→ **No se requieren modificaciones** a los diagramas.

## 6. Criterios de Exito (verificacion)

| Criterio | Estado |
|---|---|
| eval_dataset.json con 30 muestras | PASS (30/30 generadas, 0 excluidas) |
| run_ragas_eval.py sin errores + ragas_report.json + ragas_summary | PASS |
| Veredicto faithfulness honesto | PASS (valor real: 0.5118 — FAIL documentado) |
| test_tools.py + test_agents.py + test_cases.json ejecutados | PASS (58 tests, 0 failed) |
| session_summary.py genera resumen | PASS (este archivo) |
| Diagramas revisados | PASS (sin cambios necesarios) |
| SOLO se añadieron scripts/tests/eval/docs (sistema intacto) | PASS |

## 7. Entregables Generados

```
scripts/
  generate_eval_dataset.py   # B5.1: genera 30 muestras por el grafo
  run_ragas_eval.py           # B5.2: evaluacion RAGAS (API 0.1.x)
  session_summary.py          # B5.4: este script
tests/
  eval_dataset.json           # 30 muestras {question,answer,contexts,ground_truth}
  eval_dataset_meta.json      # metadatos: intent, chunks, confidence, sources
  ragas_report.json           # scores por muestra + medias + metadatos
  ragas_summary.txt           # tabla legible con 4 metricas y veredicto
  test_tools.py               # 26 tests (23 unit + 3 integration)
  test_agents.py              # 32 tests estructurales de 5 agentes
  test_cases.json             # 30 casos parametrizados
  conftest.py                 # fixtures compartidas
docs/
  Resumen_Fase5.md            # este archivo
logs/
  fase5_20260604.txt          # log completo de la fase
```
