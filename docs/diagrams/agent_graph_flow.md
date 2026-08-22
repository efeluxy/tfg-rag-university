# Flujo del Grafo de Agentes — LangGraph
> Generado al completar la Fase 3B

```mermaid
flowchart TD
    START(["__start__"]) --> ROUTER

    ROUTER["<b>Router</b><br/>Clasifica intent<br/>Extrae key_points<br/>Detecta si necesita expediente"]

    GUARDRAIL["<b>Guardrail</b><br/>Evalúa seguridad temática<br/>Clasifica nivel emocional 0-3<br/>Bloquea OUT_OF_SCOPE"]

    RETRIEVER["<b>Retriever</b><br/>Genera queries optimizadas<br/>Búsqueda híbrida Azure AI Search<br/>Devuelve chunks con metadatos"]

    STUDENT_DATA["<b>Student Data</b><br/>Verifica permisos por rol<br/>Consulta SQLite<br/>Sin llamada al LLM"]

    GENERATOR["<b>Generator</b><br/>Sintetiza el State completo<br/>Genera respuesta con GPT-4o<br/>Cita fuentes documentales"]

    END_NODE(["__end__"])

    ROUTER -->|siempre| GUARDRAIL

    GUARDRAIL -->|guardrail_triggered = True| GENERATOR
    GUARDRAIL -->|guardrail_triggered = False| RETRIEVER

    RETRIEVER -->|requires_student_data + user_id| STUDENT_DATA
    RETRIEVER -->|sin expediente necesario| GENERATOR

    STUDENT_DATA --> GENERATOR
    GENERATOR --> END_NODE
```

## Descripción del flujo
Cada mensaje del usuario recorre siempre los nodos Router y Guardrail.
El Router clasifica la intención y extrae los puntos clave. El Guardrail
evalúa si la consulta es segura y está dentro del ámbito universitario.
Si el Guardrail se activa, la respuesta predefinida llega directamente
al Generator sin pasar por búsqueda ni expediente. En el flujo normal,
el Retriever busca en Azure AI Search y, si la consulta requiere datos
personales y hay un alumno identificado, el nodo Student Data carga su
expediente académico desde SQLite. El Generator siempre es el último nodo
activo antes de devolver la respuesta al usuario.
