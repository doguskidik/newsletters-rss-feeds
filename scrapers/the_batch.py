#!/usr/bin/env python3
"""
The Batch Newsletter RSS Feed Generator
Scrapes deeplearning.ai/the-batch via __NEXT_DATA__ JSON and generates RSS feed
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from lxml import etree

BASE_URL = "https://www.deeplearning.ai"
PAGE_URL = BASE_URL + "/the-batch/page/{page}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
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


def scrape_the_batch(max_pages: int = 1) -> tuple:
    """Scrape The Batch newsletter.

    Returns (articles, logo_url, icon_url).
    logo_url: wide logo for RSS <image> element
    icon_url: square icon for webfeeds:icon / itunes:image
    """
    articles = []
    total_pages = None
    logo_url = None
    icon_url = None

    for page in range(1, max_pages + 1):
        try:
            page_props = fetch_page_data(page)
            posts = page_props["posts"]
            total_pages = page_props["totalPages"]

            if logo_url is None:
                settings = page_props.get("settings", {})
                logo_url = settings.get("logo")
                icon_url = settings.get("icon")

            for post in posts:
                articles.append(parse_post(post))
            print(f"  Page {page}/{total_pages}: fetched {len(posts)} posts")
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        if total_pages is not None and page >= total_pages:
            break

    return articles, logo_url, icon_url


def _post_process(xml_bytes: bytes, icon_url: str, self_url: str) -> bytes:
    """Post-process RSS XML to fix channel link and image URL."""
    root = etree.fromstring(xml_bytes)
    channel = root.find("channel")

    # Fix channel <link>: feedgen puts self URL there; replace with website URL
    link_elem = channel.find("link")
    if link_elem is not None:
        link_elem.text = f"{BASE_URL}/the-batch/"

    # Fix <atom:link rel="self"> to correct feed URL
    ATOM_NS = "http://www.w3.org/2005/Atom"
    for atom_link in channel.findall(f"{{{ATOM_NS}}}link"):
        if atom_link.get("rel") == "self":
            atom_link.set("href", self_url)

    # Fix standard <image> to use square icon
    img_elem = channel.find("image")
    if img_elem is not None:
        url_elem = img_elem.find("url")
        if url_elem is not None:
            url_elem.text = icon_url

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def generate_feed(
    articles: list,
    output_path: str,
    logo_url: Optional[str] = None,
    icon_url: Optional[str] = None,
) -> None:
    """Generate RSS feed from articles."""
    fg = FeedGenerator()
    fg.title("The Batch Newsletter")
    fg.link(href=f"{BASE_URL}/the-batch/", rel="alternate")
    fg.link(href="https://doguskidik.github.io/newsletters-rss-feeds/feeds/the_batch.xml", rel="self")
    fg.description("AI news and insights from deeplearning.ai")
    fg.language("en")

    if logo_url:
        fg.image(url=logo_url, title="The Batch Newsletter", link=f"{BASE_URL}/the-batch/")

    for article in articles:
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        image = article.get("image")
        if image:
            description = f'<img src="{image}" alt="{article["title"]}"><br>{article["description"]}'
        else:
            description = article["description"]
        fe.description(description)
        fe.published(article["pub_date"])
        fe.guid(article["link"], permalink=True)

    xml_bytes = fg.rss_str(pretty=True)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        owner, repo_name = repo.split("/", 1)
        self_url = f"https://{owner}.github.io/{repo_name}/feeds/the_batch.xml"
    else:
        self_url = ""
    xml_bytes = _post_process(xml_bytes, FEED_ICON_URL, self_url)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(xml_bytes)

    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Total articles: {len(articles)}")


def main():
    print("Scraping The Batch newsletter...")
    articles, logo_url, icon_url = scrape_the_batch(max_pages=1)

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "the_batch.xml")
        generate_feed(articles, output_path, logo_url, icon_url)
    else:
        print("⚠ No articles found")


if __name__ == "__main__":
    main()
