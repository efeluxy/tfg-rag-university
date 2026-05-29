"""Inicialización de clientes Azure. Las credenciales se leen de variables de entorno."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_search_client():
    """Devuelve un SearchClient configurado para el índice principal.

    Returns:
        SearchClient: cliente listo para ejecutar búsquedas.

    Raises:
        ValueError: si alguna variable de entorno requerida está vacía.
    """
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential

    endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT", "")
    key = os.getenv("AZURE_SEARCH_API_KEY", "")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "university-corpus")

    if not endpoint:
        raise ValueError("AZURE_SEARCH_SERVICE_ENDPOINT no está configurado en .env")
    if not key:
        raise ValueError("AZURE_SEARCH_API_KEY no está configurado en .env")

    return SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))


def get_index_client():
    """Devuelve un SearchIndexClient para gestión del índice (creación, borrado).

    Returns:
        SearchIndexClient: cliente de administración de índices.

    Raises:
        ValueError: si alguna variable de entorno requerida está vacía.
    """
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential

    endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT", "")
    key = os.getenv("AZURE_SEARCH_API_KEY", "")

    if not endpoint:
        raise ValueError("AZURE_SEARCH_SERVICE_ENDPOINT no está configurado en .env")
    if not key:
        raise ValueError("AZURE_SEARCH_API_KEY no está configurado en .env")

    return SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def get_openai_client():
    """Devuelve un cliente AzureOpenAI para generación de texto y embeddings.

    Returns:
        AzureOpenAI: cliente configurado con endpoint y API key.

    Raises:
        ValueError: si alguna variable de entorno requerida está vacía.
    """
    from openai import AzureOpenAI

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT no está configurado en .env")
    if not key:
        raise ValueError("AZURE_OPENAI_API_KEY no está configurado en .env")

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
        timeout=30.0,
        max_retries=2,
    )
