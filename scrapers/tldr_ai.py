#!/usr/bin/env python3
"""
TLDR AI Newsletter RSS Feed Generator
Scrapes tldr.tech/ai/{YYYY-MM-DD} pages and generates RSS feed
"""

import os
import time
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from lxml import etree

BASE_URL = "https://tldr.tech"
FEED_URL = BASE_URL + "/ai"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
FEED_ICON_URL = "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://tldr.tech&size=128"
MAX_ISSUES = 30


def fetch_issue(date) -> dict:
    """Fetch a single TLDR AI issue by date. Returns None if not found."""
    date_str = date.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/ai/{date_str}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.content, "html.parser")

    def og(prop):
        tag = soup.find("meta", property=f"og:{prop}")
        return tag["content"] if tag and tag.get("content") else None

    title = og("title") or f"TLDR AI {date_str}"

    # Extract all story articles for rich HTML content
    articles = soup.find_all("article", class_="mt-3")
    stories_html = ""
    story_titles = []
    for art in articles:
        h3 = art.find("h3")
        body = art.find("div", class_="newsletter-html")
        if h3:
            story_title = h3.get_text(strip=True)
            story_titles.append(story_title)
            link_tag = art.find("a", class_="font-bold")
            href = link_tag["href"] if link_tag and link_tag.get("href") else "#"
            summary = body.get_text(strip=True) if body else ""
            stories_html += f'<h4><a href="{href}">{story_title}</a></h4><p>{summary}</p>'

    description = "; ".join(story_titles[:5]) if story_titles else title
    html = stories_html if stories_html else f"<p>{title}</p>"

    pub_date = datetime(date.year, date.month, date.day, 12, 0, 0, tzinfo=timezone.utc)

    return {
        "url": url,
        "title": title,
        "description": description,
        "html": html,
        "pub_date": pub_date,
    }


def scrape_tldr_ai() -> list:
    """Scrape recent TLDR AI issues by iterating recent weekdays."""
    articles = []
    date = datetime.now(tz=timezone.utc).date()
    checked = 0
    max_checks = 90  # look back up to 90 days

    while len(articles) < MAX_ISSUES and checked < max_checks:
        if date.weekday() < 5:  # weekdays only
            issue = fetch_issue(date)
            if issue:
                articles.append(issue)
                print(f"  [{len(articles)}/{MAX_ISSUES}] {date} — {issue['title'][:55]}")
                time.sleep(0.2)
            checked += 1
        date -= timedelta(days=1)

    return articles


def _get_self_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        owner, repo_name = repo.split("/", 1)
        return f"https://{owner}.github.io/{repo_name}/feeds/tldr_ai.xml"
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
    fg.title("TLDR AI")
    fg.link(href=FEED_URL, rel="alternate")
    fg.link(href=self_url, rel="self")
    fg.description("Daily AI news and insights from TLDR")
    fg.language("en")
    fg.image(url=FEED_ICON_URL, title="TLDR AI", link=FEED_URL)
    fg.ttl(360)

    for article in articles:
        fe = fg.add_entry(order='append')
        fe.title(article["title"])
        fe.link(href=article["url"])
        fe.description(article["description"])
        fe.content(content=article["html"], type="html")
        fe.published(article["pub_date"])
        fe.guid(article["url"], permalink=True)

    xml_bytes = fg.rss_str(pretty=True)
    xml_bytes = _post_process(xml_bytes)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(xml_bytes)

    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Total issues: {len(articles)}")


def main():
    print("Scraping TLDR AI...")
    articles = scrape_tldr_ai()

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "tldr_ai.xml")
        generate_feed(articles, output_path)
    else:
        print("⚠ No issues found")


if __name__ == "__main__":
    main()
