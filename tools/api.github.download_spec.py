# tools/api.github.download_spec.py
"""
Optional helper: downloads GitHub's OpenAPI spec and stores it in tools/api.github.json
Run this once if you want the OpenAPI toolset to generate GitHub tools locally.
"""
import requests
import os

DEST = os.path.join(os.path.dirname(__file__), "api.github.com.json")
URL = "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"

def fetch():
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    with open(DEST, "wb") as f:
        f.write(r.content)
    print("Saved spec to", DEST)

if __name__ == "__main__":
    fetch()
