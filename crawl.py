from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import requests


def get_html(url):
    response = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    if response.status_code >= 400:
        raise Exception(f"HTTP error: {response.status_code}")
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        raise Exception(f"unexpected content type: {content_type}")
    return response.text


def normalize_url(url):
    parsed = urlparse(url)
    return (parsed.netloc + parsed.path).rstrip("/")


def get_heading_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("h1") or soup.find("h2")
    return tag.get_text() if tag else ""


def get_first_paragraph_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    tag = (main or soup).find("p")
    return tag.get_text() if tag else ""


def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for tag in soup.find_all("a"):
        href = tag.get("href")
        if href:
            urls.append(urljoin(base_url, href))
    return urls


def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for tag in soup.find_all("img"):
        src = tag.get("src")
        if src:
            urls.append(urljoin(base_url, src))
    return urls


def extract_page_data(html, page_url):
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }


class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=5, max_pages=100):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.page_data = {}
        self.visited = set()  # claimed URLs — separate from page_data so only successful fetches land there
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False
            if normalized_url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url):
        async with self.session.get(url, headers={"User-Agent": "BootCrawler/1.0"}) as response:
            if response.status >= 400:
                raise Exception(f"HTTP error: {response.status}")
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                raise Exception(f"unexpected content type: {content_type}")
            return await response.text()

    async def crawl_page(self, current_url):
        if self.should_stop:
            return

        if urlparse(current_url).netloc != self.base_domain:
            return

        normalized = normalize_url(current_url)
        if not await self.add_page_visit(normalized):
            return

        async with self.semaphore:
            print(f"crawling: {current_url}")
            try:
                html = await self.get_html(current_url)
            except Exception as e:
                print(f"  error: {e}")
                return

            data = extract_page_data(html, current_url)

            async with self.lock:
                self.page_data[normalized] = data

        tasks = []
        for link in data["outgoing_links"]:
            if not self.should_stop:
                task = asyncio.create_task(self.crawl_page(link))
                self.all_tasks.add(task)
                tasks.append(task)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            for task in tasks:
                self.all_tasks.discard(task)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url, max_concurrency=5, max_pages=100):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
