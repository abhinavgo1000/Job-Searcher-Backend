import os
from pydantic import BaseModel
import requests
from agents import function_tool

class SerperResult(BaseModel):
    title: str
    link: str
    snippet: str

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_API_URL = "https://google.serper.dev/search"

@function_tool(strict_mode=False)
def serper_web_search(query: str, num_results: int = 5) -> list[SerperResult]:
    """
    Perform a web search using Serper API and return the top results.
    """
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num_results
    }
    response = requests.post(SERPER_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    # Map API results to SerperResult models
    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append(SerperResult(
            title=item.get("title", ""),
            link=item.get("link", ""),
            snippet=item.get("snippet", "")
        ))
    return results
