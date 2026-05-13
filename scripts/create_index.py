"""Crea (o recrea) el índice 'university-corpus' en Azure AI Search."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging — consola + archivo
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"fase2_{datetime.now().strftime('%Y%m%d')}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger("create_index")

# ---------------------------------------------------------------------------
# Imports Azure
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from src.config.azure_config import get_index_client


def build_index_definition() -> SearchIndex:
    """Construye la definición completa del índice según Sección 17.1."""
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="es.microsoft",
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="source_file",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="page_number",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="section",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="last_updated",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="chunk_index",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        SimpleField(
            name="degree_relevance",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters=HnswParameters(
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                    metric="cosine",
                ),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    semantic_config = SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content")],
            title_field=SemanticField(field_name="title"),
            keywords_fields=[SemanticField(field_name="section")],
        ),
    )

    semantic_search = SemanticSearch(
        configurations=[semantic_config],
        default_configuration_name="semantic-config",
    )

    return SearchIndex(
        name="university-corpus",
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def main() -> None:
    logger.info("=== Iniciando creación del índice 'university-corpus' ===")

    client: SearchIndexClient = get_index_client()

    # Eliminar si ya existe
    existing = [idx.name for idx in client.list_indexes()]
    if "university-corpus" in existing:
        client.delete_index("university-corpus")
        logger.info("Índice existente 'university-corpus' eliminado.")

    index_def = build_index_definition()
    result = client.create_index(index_def)

    num_fields = len(result.fields)
    msg = f"Índice 'university-corpus' creado correctamente con {num_fields} campos definidos."
    print(msg)
    logger.info(msg)
    logger.info("=== Creación de índice completada ===")


if __name__ == "__main__":
    main()
