# Arquitectura de Datos — Pipeline RAG
> Generado al completar la Fase 2: Azure AI Search e Indexación

```mermaid
flowchart TD
    A[data/corpus/\n19 archivos .md] --> B[index_documents.py]
    B --> C{Chunking\ntiktoken\n512 tokens / 50 overlap}
    C --> D[Extracción\nde metadatos\ntitle, section, category...]
    D --> E[Azure OpenAI\ntext-embedding-3-large\ndim=3072]
    E --> F[(Azure AI Search\nÍndice: university-corpus\nBúsqueda híbrida)]

    G[Usuario hace\npregunta] --> H[AzureSearchTool\nsrc/tools/azure_search.py]
    H --> I[Generar embedding\nde la query]
    I --> J{Búsqueda híbrida\nVectorial + Semántica}
    F --> J
    J --> K[Top-K chunks\ncon metadatos y score]
    K --> L[Agente Retriever\nsrc/agents/retriever.py]
    L --> M[retrieved_docs\nen el State]
```

## Descripción
El pipeline RAG del sistema universitario consta de dos fases diferenciadas.
En la fase de indexación, los 19 documentos del corpus se dividen en chunks
de 512 tokens con tiktoken, se enriquecen con metadatos estructurados y se
vectorizan con text-embedding-3-large antes de subirse al índice de Azure
AI Search. En la fase de recuperación, cada consulta del usuario pasa por
la misma vectorización y se ejecuta una búsqueda híbrida que combina
similitud vectorial y comprensión semántica, devolviendo los fragmentos
más relevantes con sus fuentes para que el Agente Generador pueda
fundamentar sus respuestas.
