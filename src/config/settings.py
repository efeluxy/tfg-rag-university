"""Constantes globales del sistema. Lee valores de variables de entorno con defaults seguros."""

import os
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIEVED_DOCS: int = int(os.getenv("MAX_RETRIEVED_DOCS", "5"))
TOP_K_DEFAULT: int = int(os.getenv("TOP_K_DEFAULT", "5"))
RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.7"))
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 50
EMBEDDING_MODEL: str = "text-embedding-3-large"
EMBEDDING_DIMENSIONS: int = 3072
INDEX_NAME: str = os.getenv("AZURE_SEARCH_INDEX_NAME", "university-corpus")
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/database/students.db")
CONVERSATIONS_DB_PATH: str = "data/database/conversations.db"
LOG_DIR: str = "logs"
DIAGRAMS_DIR: str = "docs/diagrams"
