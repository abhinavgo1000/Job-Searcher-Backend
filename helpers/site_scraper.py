from bs4 import BeautifulSoup
import requests
from agents import function_tool
from pydantic import BaseModel

# Scrapy imports
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy import Request

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class ScrapeResult(BaseModel):
    url: str
    content: str

def scrape_with_bs(url: str) -> ScrapeResult:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return ScrapeResult(url=url, content=text)

def scrape_with_selenium(url: str) -> ScrapeResult:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return ScrapeResult(url=url, content=text)

class MultiPageSpider(Spider):
    name = "multi_page_spider"
    custom_settings = {
        "LOG_ENABLED": False
    }

    def __init__(self, start_url, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.max_pages = max_pages
        self.visited = set()
        self.results = []

    def parse(self, response, *args, **kwargs):
        if len(self.visited) >= self.max_pages:
            return
        self.visited.add(response.url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        self.results.append({"url": response.url, "content": text})

        next_page = response.css('a.next::attr(href)').get()
        if next_page and len(self.visited) < self.max_pages:
            yield Request(response.urljoin(next_page), callback=self.parse)

def scrape_with_scrapy(start_url: str, max_pages: int = 5) -> list[ScrapeResult]:
    process = CrawlerProcess(settings={"LOG_ENABLED": False})
    spider = MultiPageSpider(start_url, max_pages=max_pages)
    process.crawl(spider)
    process.start()
    return [ScrapeResult(url=item["url"], content=item["content"]) for item in spider.results]

@function_tool(strict_mode=False)
def scrape_page_content(url: str, method: str = "bs", max_pages: int = 5) -> list[ScrapeResult]:
    """
    Scrapes visible text from a web page using the specified method.
    Supported methods: 'bs' (BeautifulSoup), 'selenium', 'scrapy'
    For 'scrapy', follows 'next' links up to max_pages.
    """
    if method == "bs":
        return [scrape_with_bs(url)]
    elif method == "selenium":
        return [scrape_with_selenium(url)]
    elif method == "scrapy":
        return scrape_with_scrapy(url, max_pages)
    else:
        raise ValueError("Unsupported method. Use 'bs', 'selenium', or 'scrapy'.")
