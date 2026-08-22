# Arquitectura de Datos — Pipeline RAG
> Generado al completar la Fase 2: Azure AI Search e Indexación

```mermaid
flowchart TD
    A[data/corpus/<br/>22 archivos .md<br/>20.232 palabras] --> B[index_documents.py]
    B --> C{Chunking<br/>tiktoken cl100k_base<br/>512 tokens / 50 overlap}
    C --> D[Extracción de metadatos<br/>title, section, category,<br/>source_file, degree_relevance]
    D --> E[Azure OpenAI<br/>text-embedding-3-large<br/>dim=3072]
    E --> F[(Azure AI Search<br/>university-corpus<br/>94 chunks · HNSW coseno)]

    G([Usuario hace<br/>pregunta]) --> H[Agente Retriever<br/>retriever.py]
    H --> I[Expansión con sinónimos<br/>synonyms.py]
    I --> J[AzureSearchTool<br/>azure_search.py]
    J --> K[Generar embedding<br/>de la query]
    K --> L{Búsqueda híbrida<br/>Vectorial + Semántica}
    F --> L
    L --> M[Top-K chunks con<br/>metadatos y score<br/>k=5 · k=10 si enumerativa]
    M --> N[retrieved_docs<br/>en el State]
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
