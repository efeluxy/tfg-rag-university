# Flujo del Grafo de Agentes — LangGraph
> Generado al completar la Fase 3B

```mermaid
flowchart TD
    START([__start__]) --> ROUTER

    ROUTER["`**Router**
    Clasifica intent
    Extrae key_points
    Detecta si necesita expediente`"]

    GUARDRAIL["`**Guardrail**
    Evalúa seguridad
    Detecta crisis emocional
    Bloquea OUT_OF_SCOPE`"]

    RETRIEVER["`**Retriever**
    Genera queries optimizadas
    Búsqueda híbrida Azure AI Search
    Devuelve chunks con metadatos`"]

    STUDENT_DATA["`**Student Data**
    Consulta SQLite
    Carga expediente completo
    Solo si user_id presente`"]

    GENERATOR["`**Generator**
    Sintetiza State completo
    Genera respuesta con GPT-4o
    Cita fuentes documentales`"]

    END_NODE([__end__])

    ROUTER -->|siempre| GUARDRAIL

    GUARDRAIL -->|guardrail_triggered = True| GENERATOR
    GUARDRAIL -->|guardrail_triggered = False| RETRIEVER

    RETRIEVER -->|requires_student_data + user_id| STUDENT_DATA
    RETRIEVER -->|sin expediente necesario| GENERATOR

    STUDENT_DATA --> GENERATOR
    GENERATOR --> END_NODE

    style ROUTER       fill:#2E75B6,color:#fff,stroke:#1F4E8A
    style GUARDRAIL    fill:#C55A11,color:#fff,stroke:#843D0C
    style RETRIEVER    fill:#2E75B6,color:#fff,stroke:#1F4E8A
    style STUDENT_DATA fill:#7030A0,color:#fff,stroke:#4B1D6B
    style GENERATOR    fill:#375623,color:#fff,stroke:#233B17
    style START        fill:#1F4E8A,color:#fff,stroke:#1F4E8A
    style END_NODE     fill:#1F4E8A,color:#fff,stroke:#1F4E8A
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
