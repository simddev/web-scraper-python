# Web Crawler

A concurrent web crawler CLI that crawls a website and exports a JSON report of every page it visits.

## Features

- Async concurrent crawling via `aiohttp` and `asyncio`
- HTML parsing with `BeautifulSoup4` — extracts headings, paragraphs, links, and images
- URL normalization to avoid visiting the same page twice
- Stays within the target domain
- Configurable concurrency and page limits
- JSON report output

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
uv venv
source .venv/bin/activate
uv sync
```

## Usage

```bash
uv run main.py <url> <max_concurrency> <max_pages>
```

**Arguments**

| Argument | Description |
|---|---|
| `url` | The starting URL to crawl |
| `max_concurrency` | Maximum number of simultaneous requests |
| `max_pages` | Maximum number of pages to crawl |

**Example**

```bash
uv run main.py https://example.com 5 50
```

This will crawl up to 50 pages of `example.com` with 5 concurrent requests and write the results to `report.json`.

## Output

After crawling, `report.json` is created in the current directory. It contains a sorted list of page records:

```json
[
  {
    "url": "https://example.com/about",
    "heading": "About Us",
    "first_paragraph": "We build things.",
    "outgoing_links": ["https://example.com/", "https://example.com/contact"],
    "image_urls": ["https://example.com/logo.png"]
  }
]
```

## Running Tests

```bash
uv run -m unittest
```
