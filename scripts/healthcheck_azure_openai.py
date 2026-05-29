"""Block 3.1 + 3.2: Azure OpenAI healthcheck (chat + embeddings)."""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.azure_config import get_openai_client

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

def test_chat():
    client = get_openai_client()
    t0 = time.time()
    r = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": "Responde solo OK"}],
        max_tokens=10,
        timeout=30,
    )
    elapsed = time.time() - t0
    content = r.choices[0].message.content.strip()
    print(f"AZURE_OPENAI_CHAT: {content} ({elapsed:.1f}s)")
    return True

def test_embeddings():
    client = get_openai_client()
    t0 = time.time()
    r = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input="test de embeddings",
    )
    elapsed = time.time() - t0
    dims = len(r.data[0].embedding)
    print(f"AZURE_OPENAI_EMBEDDINGS: dims={dims} ({elapsed:.1f}s)")
    assert dims == 3072, f"Expected 3072 dims, got {dims}"
    return True

if __name__ == "__main__":
    ok = 0
    try:
        test_chat()
        ok += 1
    except Exception as e:
        print(f"AZURE_OPENAI_CHAT ERROR: {e}")

    try:
        test_embeddings()
        ok += 1
    except Exception as e:
        print(f"AZURE_OPENAI_EMBEDDINGS ERROR: {e}")

    print(f"TOTAL: {ok}/2")
    sys.exit(0 if ok == 2 else 1)
