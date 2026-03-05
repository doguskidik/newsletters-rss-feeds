#!/usr/bin/env python3
"""
The Rundown AI Newsletter RSS Feed Generator
Scrapes therundown.ai via sitemap + Open Graph metadata
"""

import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from lxml import etree

BASE_URL = "https://www.therundown.ai"
SITEMAP_URL = BASE_URL + "/sitemap.xml"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
FEED_URL = BASE_URL + "/"
FEED_ICON_URL = "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://therundown.ai&size=128"
MAX_POSTS = 50


def fetch_sitemap_posts() -> list:
    """Fetch post URLs and lastmod dates from sitemap, return newest MAX_POSTS."""
    resp = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    posts = []
    for url_elem in root.findall("sm:url", ns):
        loc_elem = url_elem.find("sm:loc", ns)
        lastmod_elem = url_elem.find("sm:lastmod", ns)
        if loc_elem is None:
            continue
        loc = loc_elem.text
        lastmod = lastmod_elem.text if lastmod_elem is not None else ""
        if "/p/" in loc:
            posts.append({"url": loc, "lastmod": lastmod})

    posts.sort(key=lambda x: x["lastmod"], reverse=True)
    return posts[:MAX_POSTS]


def fetch_post(url: str) -> dict:
    """Fetch post metadata via Open Graph and JSON-LD."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")

    def og(prop):
        tag = soup.find("meta", property=f"og:{prop}")
        return tag["content"] if tag and tag.get("content") else None

    def meta(name):
        tag = soup.find("meta", attrs={"name": name})
        return tag["content"] if tag and tag.get("content") else None

    title = og("title") or (soup.find("title").get_text(strip=True) if soup.find("title") else url)
    description = og("description") or meta("description") or ""
    image = og("image")

    pub_time = meta("article:published_time") or og("article:published_time")
    if not pub_time:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                pub_time = data.get("datePublished")
                if pub_time:
                    break
            except (json.JSONDecodeError, AttributeError):
                pass

    try:
        pub_date = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, AttributeError):
        pub_date = datetime.now(tz=timezone.utc)

    return {
        "url": url,
        "title": title,
        "description": description,
        "image": image,
        "pub_date": pub_date,
    }


def scrape_the_rundown_ai() -> list:
    """Scrape the most recent posts from The Rundown AI."""
    print(f"  Fetching sitemap...")
    posts = fetch_sitemap_posts()
    print(f"  Found {len(posts)} recent posts in sitemap")

    articles = []
    for i, post in enumerate(posts, 1):
        try:
            article = fetch_post(post["url"])
            articles.append(article)
            print(f"  [{i}/{len(posts)}] {article['title'][:60]}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [{i}/{len(posts)}] Error fetching {post['url']}: {e}")

    articles.sort(key=lambda x: x["pub_date"], reverse=True)
    return articles


def _get_self_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        owner, repo_name = repo.split("/", 1)
        return f"https://{owner}.github.io/{repo_name}/feeds/the_rundown_ai.xml"
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
    fg.title("The Rundown AI")
    fg.link(href=FEED_URL, rel="alternate")
    fg.link(href=self_url, rel="self")
    fg.description("Your daily AI news and insights")
    fg.language("en")
    fg.image(url=FEED_ICON_URL, title="The Rundown AI", link=FEED_URL)
    fg.ttl(360)

    for article in articles:
        fe = fg.add_entry(order='append')
        fe.title(article["title"])
        fe.link(href=article["url"])
        fe.description(article["description"])
        image = article.get("image")
        if image:
            html = f'<img src="{image}" alt="{article["title"]}"><br><p>{article["description"]}</p>'
        else:
            html = f'<p>{article["description"]}</p>'
        fe.content(content=html, type="html")
        fe.published(article["pub_date"])
        fe.guid(article["url"], permalink=True)

    xml_bytes = fg.rss_str(pretty=True)
    xml_bytes = _post_process(xml_bytes)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(xml_bytes)

    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Total articles: {len(articles)}")


def main():
    print("Scraping The Rundown AI...")
    articles = scrape_the_rundown_ai()

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "the_rundown_ai.xml")
        generate_feed(articles, output_path)
    else:
        print("⚠ No articles found")


if __name__ == "__main__":
    main()
