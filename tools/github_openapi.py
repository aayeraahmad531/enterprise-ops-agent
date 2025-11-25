"""
Minimal GitHub OpenAPI-style wrapper for demo purposes.
In a real ADK project you'd generate tools from an OpenAPI spec,
or use the ADK OpenAPI toolset. Here we keep it simple.
"""
import requests
import os
import logging

logger = logging.getLogger("github_tool")

class GitHubOpenAPI:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN", "")
        self.base = "https://api.github.com"

    def search_issues(self, query: str):
        url = f"{self.base}/search/issues"
        headers = {"Accept":"application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        params = {"q": query, "per_page": 10}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning("GitHub API non-200: %s %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
        return data.get("items", [])
