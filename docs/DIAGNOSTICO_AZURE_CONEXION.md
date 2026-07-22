# Diagnóstico Azure vs Código — Informe final

**Fecha:** 2026-07-11
**Rama:** `fase-5-bis`
**Modo:** solo lectura (sin modificar `src/`, `app/`, `data/`, `tests/`, `docs/`, `.env`)
**Log de evidencia:** `logs/diagnostico_azure_20260711.txt`
**Script de diagnóstico:** `scripts/diag_azure_connection.py` (temporal, eliminable sin impacto)

---

## 1. Resumen del síntoma

En la interfaz Streamlit, en modo administrador sin alumno seleccionado:

- La consulta `"hola"` responde correctamente (conocimiento general).
- Una consulta que requiere recuperación documental o datos de alumno
  (p. ej. `"quiero saber como se llama el alumno ALU001"`) devuelve el mensaje genérico:
  > "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, inténtalo de nuevo."

**Sospecha inicial:** cuota gratuita mensual del *semantic ranker* de Azure AI Search agotada.
**Resultado del diagnóstico:** la sospecha queda **DESCARTADA**. La causa real es distinta (ver §4).

---

## 2. Resultado por bloque

| Bloque | Descripción | Veredicto | Evidencia clave |
|--------|-------------|-----------|-----------------|
| 0 | Preparación | **PASS** | venv activo, Python 3.10.0, rama `fase-5-bis`, log creado. |
| 1 | Origen del mensaje genérico | **PASS** | `app/components/chat.py:49-59`: `except Exception` que envuelve `graph.invoke()` y oculta la excepción real. |
| 2 | Cadena Retriever → azure_search | **PASS** | `azure_search.py` usa `query_type="semantic"` + `semantic-config`; **sin** `try/except` ni en `azure_search.py` ni en `retriever.py`; **sin** fallback no-semántico. |
| 3 | Configuración Azure (presencia) | **PASS** | Las 8 variables Azure críticas presentes y no vacías (valores nunca impresos). |
| 4 | Búsqueda **NO** semántica (conexión real) | **FAIL** | `HttpResponseError: The search service 'tfg-search-felix' is disabled.` |
| 5 | Búsqueda **CON** semantic ranker | **PASS** (captura) | Mismo error exacto que el Bloque 4 → **no** es cuota semántica. |
| 6 | Reproducción de la consulta real | **PASS** (captura) | Traceback real: origen en nodo **retriever** → `azure_search.py:72`. |

---

## 3. Cadena técnica del fallo (Bloques 1-2)

```
Consulta con recuperación
  -> nodo retriever            src/agents/retriever.py:121  (sin try/except)
     -> search_knowledge_base  src/tools/azure_search.py:62/72  (sin try/except)
        -> search_client.search(query_type="semantic", semantic-config)
           -> azure.core.exceptions.HttpResponseError  (servicio deshabilitado)
  -> la excepción sube por el grafo
     -> graph.invoke()
        -> app/components/chat.py:49  except Exception
           -> mensaje genérico visible al usuario  (oculta la causa real)
```

El punto donde la excepción de Azure se transforma en el mensaje genérico es
`app/components/chat.py:49`. El `logger.error(..., exc_info=True)` registra el
traceback real en el log de la app, pero al usuario solo le llega el mensaje genérico.

---

## 4. Hallazgo clave (Bloques 4-6)

El error real, **idéntico con y sin semantic ranker**, es:

```
HttpResponseError: The search service 'tfg-search-felix' is disabled.
```

Evidencias que descartan la hipótesis de cuota semántica y descartan fallo de código:

1. **El Bloque 4 (SIN semantic ranker) también falla** con el mismo mensaje.
   Si fuese cuota del *semantic ranker*, la búsqueda no-semántica habría funcionado.
2. **El embedding de Azure OpenAI se genera correctamente** antes de la búsqueda
   (el error proviene de `search`, no de `embeddings.create`). → **Azure OpenAI está operativo.**
   Solo Azure AI Search está afectado. Esto explica por qué `"hola"` responde (no usa el
   retriever, solo OpenAI) y las consultas con recuperación fallan.
3. **No es fallo de código ni de configuración:** el endpoint resolvió, la petición llegó
   al servicio, y Azure respondió con un error de **estado del recurso** (`disabled`),
   no un `401/403` (auth), ni `404` (índice inexistente), ni error de red. La key, el
   endpoint y el nombre de índice del código son **correctos**.

**Causa raíz:** el recurso **Azure AI Search `tfg-search-felix` está DESHABILITADO**
a nivel de Azure. Causas típicas: suscripción Free/estudiante suspendida o expirada,
servicio deshabilitado por inactividad/facturación, o deshabilitado manualmente en el portal.

---

## 5. Árbol de decisión aplicado

- Búsqueda NO semántica **OK** + semántica falla con error de cuota
  → *CÓDIGO OK (cuota del semantic ranker).* — **No aplica.**
- Búsqueda NO semántica **FALLA** (auth/endpoint/índice)
  → *CÓDIGO/CONFIG CON FALLO.* — **No aplica en sentido estricto:** la búsqueda no
  semántica falla, pero **no** por auth/endpoint/índice mal configurados, sino porque
  el **servicio Azure está deshabilitado** (estado del recurso). El código de conexión
  es correcto.
- **Caso real:** el servicio de Azure AI Search está deshabilitado a nivel de recurso.
  → El código y la configuración son correctos; el problema es la **infraestructura Azure**.

---

## 6. Acción recomendada (fuera del alcance solo-lectura)

1. Entrar al **Azure Portal** y revisar el estado del recurso `tfg-search-felix`
   (*Search service*) y de la **suscripción** asociada.
2. **Re-habilitar** el servicio / reactivar la suscripción. Si la suscripción Free de
   estudiante expiró, migrar el recurso o crear uno nuevo y **re-indexar** el corpus.
3. Solo **después** tendría sentido evaluar la cuota del *semantic ranker* y añadir un
   fallback no-semántico (FASE 0.1). **No es el problema actual.**

Mejora de robustez opcional (no aplicada, requiere tocar código): envolver la llamada
a Azure Search en `azure_search.py`/`retriever.py` con `try/except` para degradar con
un mensaje específico en vez del genérico, y así no ocultar la causa real al usuario.

---

## 7. Veredicto global

> **VEREDICTO: CÓDIGO OK.** El error **no** es de código ni de conexión mal configurada,
> y **tampoco** es la cuota del *semantic ranker*. La causa es que el **servicio Azure AI
> Search `tfg-search-felix` está DESHABILITADO** a nivel de recurso Azure. El código de
> conexión (endpoint, key, índice) es correcto y Azure OpenAI funciona. **Acción:**
> re-habilitar el servicio de Search / revisar la suscripción en el Azure Portal.

---

*Notas: no se hizo `git commit`; rama sin cambios (`fase-5-bis`); no se modificó ningún
archivo del sistema. El script `scripts/diag_azure_connection.py` puede eliminarse sin impacto.*
