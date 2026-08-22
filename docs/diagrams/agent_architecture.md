# Arquitectura de Agentes
> Generado al completar la Fase 3B

```mermaid
graph LR
    subgraph CAPA_ORQUESTACION["Capa de Orquestación — LangGraph"]
        R[Router]
        G[Guardrail]
        RET[Retriever]
        SD[Student Data]
        GEN[Generator]
    end

    subgraph CAPA_PROMPTS["Prompts"]
        PR[router_prompt.py]
        PG[guardrail_prompt.py]
        PRET[retriever_prompt.py]
        PGEN[generator_prompt.py<br/>+ persona.py]
    end

    subgraph CAPA_TOOLS["Herramientas"]
        AZ[AzureSearchTool<br/>azure_search.py]
        SQL[SQLiteTool<br/>sqlite_query.py]
        LLM[Azure OpenAI<br/>GPT-4o]
    end

    subgraph CAPA_DATOS["Capa de Datos"]
        IDX[(Azure AI Search<br/>university-corpus<br/>94 chunks)]
        DB[(SQLite<br/>students.db<br/>50 alumnos)]
    end

    R --> PR
    R --> LLM
    G --> PG
    G --> LLM
    RET --> PRET
    RET --> LLM
    RET --> AZ
    SD --> SQL
    GEN --> PGEN
    GEN --> LLM

    AZ --> IDX
    SQL --> DB
```

## Descripción
El sistema se organiza en cuatro capas diferenciadas. La capa de
orquestación contiene los cinco agentes implementados como nodos
LangGraph. Cada agente que necesita razonamiento de lenguaje natural
llama a GPT-4o a través de Azure OpenAI usando su prompt específico.
Los agentes Retriever y Student Data acceden a las capas de datos
mediante tools dedicadas: AzureSearchTool para la búsqueda vectorial
en el índice de Azure AI Search y SQLiteTool para la consulta del
expediente académico en la base de datos local.
