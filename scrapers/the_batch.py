#!/usr/bin/env python3
"""
The Batch Newsletter RSS Feed Generator
Scrapes deeplearning.ai/the-batch via __NEXT_DATA__ JSON and generates RSS feed
"""

import json
import os
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

BASE_URL = "https://www.deeplearning.ai"
PAGE_URL = BASE_URL + "/the-batch/page/{page}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}


def fetch_page_posts(page: int) -> tuple[list[dict], int]:
    """Fetch posts from a single page via __NEXT_DATA__ JSON.

    Returns (posts, total_pages).
    """
    url = PAGE_URL.format(page=page)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script:
        raise ValueError(f"__NEXT_DATA__ not found on {url}")

    data = json.loads(script.string)
    page_props = data["props"]["pageProps"]
    return page_props["posts"], page_props["totalPages"]


def parse_post(post: dict) -> dict:
    """Extract relevant fields from a raw post dict."""
    slug = post["slug"]
    link = f"{BASE_URL}/the-batch/{slug}/"

    published_at = post.get("published_at", "")
    try:
        pub_date = datetime.fromisoformat(published_at)
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pub_date = datetime.now(tz=timezone.utc)

    description = post.get("custom_excerpt") or post.get("excerpt") or post["title"]

    return {
        "title": post["title"],
        "link": link,
        "description": description,
        "pub_date": pub_date,
        "image": post.get("feature_image"),
    }


def scrape_the_batch(max_pages: int = 1) -> list[dict]:
    """Scrape The Batch newsletter.

    Args:
        max_pages: Number of pages to fetch (each page has ~16 issues).
    """
    articles = []
    total_pages = None

    for page in range(1, max_pages + 1):
        try:
            posts, total_pages = fetch_page_posts(page)
            for post in posts:
                articles.append(parse_post(post))
            print(f"  Page {page}/{total_pages}: fetched {len(posts)} posts")
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        if total_pages is not None and page >= total_pages:
            break

    return articles


def generate_feed(articles: list[dict], output_path: str) -> None:
    """Generate RSS feed from articles."""
    fg = FeedGenerator()
    fg.title("The Batch Newsletter")
    fg.link(href=f"{BASE_URL}/the-batch/", rel="alternate")
    fg.description("AI news and insights from deeplearning.ai")
    fg.language("en")

    for article in articles:
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article["description"])
        fe.published(article["pub_date"])
        fe.guid(article["link"], permalink=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path, pretty=True)
    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Total articles: {len(articles)}")


def main():
    print("Scraping The Batch newsletter...")
    articles = scrape_the_batch(max_pages=1)

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "the_batch.xml")
        generate_feed(articles, output_path)
    else:
        print("⚠ No articles found")


if __name__ == "__main__":
    main()
