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
from lxml import etree

BASE_URL = "https://www.deeplearning.ai"
PAGE_URL = BASE_URL + "/the-batch/page/{page}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
FEED_URL = BASE_URL + "/the-batch/"
FEED_ICON_URL = "https://www.deeplearning.ai/static/favicons/apple-touch-icon.png"


def fetch_page_data(page: int) -> dict:
    """Fetch raw pageProps from a single page via __NEXT_DATA__ JSON."""
    url = PAGE_URL.format(page=page)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script:
        raise ValueError(f"__NEXT_DATA__ not found on {url}")

    return json.loads(script.string)["props"]["pageProps"]


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


def scrape_the_batch() -> list:
    """Scrape all pages of The Batch newsletter. Returns list of articles."""
    articles = []
    page = 1

    while True:
        try:
            page_props = fetch_page_data(page)
            posts = page_props["posts"]
            total_pages = page_props["totalPages"]

            for post in posts:
                articles.append(parse_post(post))
            print(f"  Page {page}/{total_pages}: fetched {len(posts)} posts")

            if page >= total_pages:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    return articles


def _get_self_url() -> str:
    """Determine the feed's self URL from environment or fallback."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        owner, repo_name = repo.split("/", 1)
        return f"https://{owner}.github.io/{repo_name}/feeds/the_batch.xml"
    return FEED_URL


def _post_process(xml_bytes: bytes) -> bytes:
    """Fix channel <link>: feedgen sets it to self URL instead of website URL."""
    root = etree.fromstring(xml_bytes)
    channel = root.find("channel")
    link_elem = channel.find("link")
    if link_elem is not None:
        link_elem.text = FEED_URL
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def generate_feed(articles: list, output_path: str) -> None:
    """Generate RSS feed from articles."""
    self_url = _get_self_url()

    fg = FeedGenerator()
    fg.title("The Batch Newsletter")
    fg.link(href=FEED_URL, rel="alternate")
    fg.link(href=self_url, rel="self")
    fg.description("AI news and insights from deeplearning.ai")
    fg.language("en")
    fg.image(url=FEED_ICON_URL, title="The Batch Newsletter", link=FEED_URL)
    fg.ttl(360)

    for article in reversed(articles):  # newest first
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article["description"])  # plain text summary
        image = article.get("image")
        if image:
            html = f'<img src="{image}" alt="{article["title"]}"><br><p>{article["description"]}</p>'
        else:
            html = f'<p>{article["description"]}</p>'
        fe.content(content=html, type="html")  # rich HTML via <content:encoded>
        fe.published(article["pub_date"])
        fe.guid(article["link"], permalink=True)

    xml_bytes = fg.rss_str(pretty=True)
    xml_bytes = _post_process(xml_bytes)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(xml_bytes)

    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Total articles: {len(articles)}")


def main():
    print("Scraping The Batch newsletter...")
    articles = scrape_the_batch()

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "the_batch.xml")
        generate_feed(articles, output_path)
    else:
        print("⚠ No articles found")


if __name__ == "__main__":
    main()
