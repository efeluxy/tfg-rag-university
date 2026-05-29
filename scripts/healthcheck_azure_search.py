"""Block 3.3: Azure AI Search healthcheck."""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.azure_config import get_search_client

def test_search():
    client = get_search_client()
    t0 = time.time()
    results = list(client.search(search_text="*", top=1, include_total_count=True))
    elapsed = time.time() - t0
    count = len(results)
    print(f"AZURE_SEARCH: {count} doc(s) sample returned ({elapsed:.1f}s)")
    # Try to get total count
    try:
        results_full = client.search(search_text="*", top=1, include_total_count=True)
        total = results_full.get_count()
        if total is not None:
            print(f"AZURE_SEARCH_TOTAL_COUNT: {total}")
            if total == 94:
                print("AZURE_SEARCH_COUNT: PASS (94 chunks)")
            else:
                print(f"AZURE_SEARCH_COUNT: WARNING (expected 94, got {total})")
    except Exception as e:
        print(f"AZURE_SEARCH_COUNT: could not retrieve - {e}")
    return True

if __name__ == "__main__":
    try:
        test_search()
        print("AZURE_SEARCH: OK")
        sys.exit(0)
    except Exception as e:
        print(f"AZURE_SEARCH ERROR: {e}")
        sys.exit(1)
