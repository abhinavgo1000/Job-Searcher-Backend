from bs4 import BeautifulSoup
import requests
from agents import function_tool
from pydantic import BaseModel

class ScrapeResult(BaseModel):
    url: str
    content: str

@function_tool(strict_mode=False)
def scrape_page_content(url: str) -> ScrapeResult:
    """
    Fetches the HTML content of the given URL and returns the visible text.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(strip=True)
    return ScrapeResult(url=url, content=text)
