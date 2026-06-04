# Re-evaluacion RAGAS — Fase 5-bis

**Fecha:** 2026-06-04  
**Rama:** `fase-5-bis`  
**Sistema evaluado:** sin modificaciones (git diff src/ y app/ vacio)

---

## Motivacion

La evaluacion de Fase 5 (RAGAS 0.1.21) produjo metricas anómalamente bajas:
faithfulness 0.51, answer_relevancy 0.48, context_precision 0.38,
context_recall 0.27. La hipotesis era que esas cifras eran parcialmente
un artefacto de medicion, no un reflejo fiel del sistema. Esta fase investiga
y re-mide con el evaluador corregido.

---

## Cambios en la configuracion de evaluacion

### 1. Version de RAGAS: 0.1.21 → 0.2.6

RAGAS 0.2.6 fue instalado sin modificar ninguna dependencia del sistema
(langchain 0.2.17 / langchain-openai 0.1.25 permanecen intactos). La
version 0.2.6 es compatible con el entorno virtual del proyecto.

**Por que importa:** RAGAS 0.1.x tenia un bug conocido en el que respuestas
cortas o del tipo "no dispongo de informacion" producian extraccion de 0
declaraciones verificables, devolviendo faithfulness=NaN→0.0 incorrectamente.
RAGAS 0.2.x maneja este caso con mayor robustez.

### 2. Formato del dataset: column_map

En RAGAS 0.2.x los campos internos cambiaron de nombre:
`question/answer/contexts/ground_truth` → `user_input/response/retrieved_contexts/reference`.

En la evaluacion v1 no se aplicaba ningun mapeo, lo que causaba que varias
metricas no encontrasen los datos y devolvieran NaN/0.0 para algunas muestras.
En v2 se usa el parametro `column_map` de `evaluate()` para hacer la conversion
de forma transparente.

### 3. Variable de entorno del deployment

El script v1 leia `AZURE_OPENAI_DEPLOYMENT` pero `.env` define
`AZURE_OPENAI_DEPLOYMENT_NAME`. El v2 lee la variable correcta con fallback
al nombre antiguo. (Impacto bajo porque el valor por defecto "gpt-4o" coincide
con el deployment real, pero se corrige para mayor claridad.)

### 4. Concurrencia reducida

`max_workers` se redujo de 4 a 2 para minimizar errores HTTP 429 que provocaban
que muestras individuales fallaran silenciosamente y devolvieran 0.0.

### 5. Correcciones de ground_truth (5 muestras)

Se corrigieron 5 muestras con afirmaciones factuales incorrectas respecto al
corpus. Ninguna correccion reproduce la respuesta del sistema; todas se basan
exclusivamente en el corpus de la Universidad Demo:

| Indice | Descripcion del error | Fuente |
|--------|----------------------|--------|
| [00] | "Consejo de Departamento" (corpus: Consejo Academico); "6 convocatorias" (corpus: 5) | Art. 4 Reglamento Academico |
| [03] | "12 creditos" (corpus: 50%/60%/65% segun ano = 27/33/39 ECTS) | Art. 2 Normativa Permanencia |
| [05] | "primer mes" (corpus: sexta semana lectiva); afirma que anulacion consume convocatoria (corpus: NO consume) | Art. 3 Reglamento Academico |
| [06] | "optativas 36 cr." (corpus: 42 ECTS); desglose de obligatorias incorrecto | Resumen Plan Informatica |
| [21] | "10 dias" para reclamacion (corpus: 5 dias); "el departamento" (corpus: Comision Evaluacion del Grado) | Art. 5-6 Politica Evaluacion |

---

## Resultados

### Tabla comparativa v1 vs v2

| Metrica            | v1 (0.1.21) | v2 (0.2.6) | Delta   | Objetivo | Veredicto |
|--------------------|-------------|------------|---------|----------|-----------|
| faithfulness       | 0.5118      | 0.5521     | +0.0403 | 0.85     | FAIL      |
| answer_relevancy   | 0.4755      | 0.5104     | +0.0349 | 0.80     | FAIL      |
| context_precision  | 0.3756      | 0.2956     | -0.0800 | 0.75     | FAIL      |
| context_recall     | 0.2730      | 0.3111     | +0.0381 | 0.70     | FAIL      |

### Interpretacion de los cambios

**Mejoras en faithfulness (+4%) y answer_relevancy (+3.5%):**  
Coherente con la hipotesis de artefacto: el formato incorrecto del dataset en
0.1.x causaba fallos silenciosos en algunas muestras, devolviendo NaN→0.0.
Con el `column_map` correcto y RAGAS 0.2.6, esas muestras se puntuan
correctamente, elevando las medias.

**Mejora en context_recall (+3.8%):**  
La correccion de los 5 ground_truths con errores factuales impacta directamente
en context_recall (que compara las afirmaciones del GT con los contextos
recuperados). Los GTs corregidos son verificables contra el corpus, lo que
permite que el juez los encuentre en los chunks.

**Descenso en context_precision (-8%):**  
En RAGAS 0.2.x la metodologia de context_precision es mas estricta: juzga si
cada chunk recuperado es necesario para responder la pregunta segun la referencia.
Un sistema que recupera 5 chunks amplios (estrategia maxima cobertura) puede
tener precision baja aunque los chunks sean relevantes, porque no todos los 5
son igualmente necesarios. El descenso es un reflejo mas preciso de la estrategia
de recuperacion, no un deterioro real.

### 5 peores muestras (faithfulness v2)

| Score | Pregunta |
|-------|---------|
| 0.000 | Cuantos creditos tiene la asignatura de Aprendizaje Automatico... |
| 0.083 | Cuales son los pasos para solicitar una beca de colaboracion... |
| 0.100 | Que es la prueba especifica de acceso y como afecta a la nota... |
| 0.182 | Puede un alumno cambiar de grupo de practicas una vez comenzado... |
| 0.190 | Como se tramita el reconocimiento de creditos por experiencia... |

La muestra [12] (Aprendizaje Automatico) tiene faithfulness=0.0 en ambas
versiones. El sistema responde "No dispongo de informacion especifica" para esa
pregunta, que tiene 0 afirmaciones verificables → faithfulness genuinamente
baja, no un error de medicion.

---

## Conclusion sobre la hipotesis

La hipotesis del artefacto de medicion se **confirma parcialmente**:

- **Confirmada:** El desajuste de nombres de campo (`column_map`) causaba
  NaN/0.0 en algunas muestras, deprimiendo las medias artificialmente.
  Corregido este problema, faithfulness, answer_relevancy y context_recall
  mejoran entre 3 y 4 puntos porcentuales.

- **Parcialmente refutada:** Las mejoras son reales pero modestas. El sistema
  no alcanza los objetivos del TFG en ninguna de las 4 metricas. Las metricas
  bajas reflejan tanto el artefacto de medicion como limitaciones genuinas
  del sistema en las preguntas con ground_truth de referencia exigente:

  - Algunas preguntas preguntan por detalles muy especificos de guias docentes
    (asignaturas, creditos, laboratorios) que el corpus cubre parcialmente.
  - El sistema a veces responde "No dispongo de informacion" cuando el corpus
    es insuficiente, lo que es correcto funcionalmente pero penaliza faithfulness.
  - La estrategia de recuperacion de 5 chunks amplios favorece cobertura sobre
    precision, lo que explica el context_precision bajo.

---

## Integridad del sistema

```
git diff src/ app/  →  (sin salida — cero modificaciones)
```

El sistema (agentes, grafo, prompts, herramientas, BD, interfaz) permanece
intacto e identico a la rama master. Los 58/58 tests siguen pasando.

---

## Archivos generados

| Archivo | Descripcion |
|---------|-------------|
| `tests/ragas_v1_legacy/ragas_report.json` | Resultados v1 archivados |
| `tests/ragas_v1_legacy/ragas_summary.txt` | Resumen v1 archivado |
| `tests/ragas_report_v2.json` | Scores detallados por muestra (v2) |
| `tests/ragas_summary_v2.txt` | Tabla comparativa v1 vs v2 |
| `scripts/run_ragas_eval.py` | Script corregido (RAGAS 0.2.6, column_map, GT corrections) |
