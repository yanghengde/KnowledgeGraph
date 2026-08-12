import httpx
import time

try:
    start = time.time()
    resp = httpx.get("http://localhost:5050/", timeout=5.0)
    print(f"Server is ALIVE. Status: {resp.status_code}, Time taken: {time.time() - start:.3f}s")
except Exception as e:
    print(f"Server is NOT responsive: {e}")
