#!/usr/bin/env python3
"""
BBC Learning English RSS Feed Generator
Scrapes BBC Learning English and generates RSS feed
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import os


def scrape_bbc_learning():
    """Scrape BBC Learning English page"""
    url = "https://www.bbc.co.uk/learningenglish/english/"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        articles = []

        # Find all content items (adjust selectors based on actual HTML structure)
        content_items = soup.find_all('div', class_='content-item') or soup.find_all('article')

        for item in content_items[:20]:  # Limit to 20 most recent
            try:
                # Extract title
                title_elem = item.find('h2') or item.find('h3') or item.find('a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Extract link
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue

                link = link_elem['href']
                if not link.startswith('http'):
                    link = 'https://www.bbc.co.uk' + link

                # Extract description
                desc_elem = item.find('p', class_='description') or item.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else title

                # Extract date if available
                date_elem = item.find('time') or item.find('span', class_='date')
                pub_date = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pub_date = datetime.now()
                else:
                    pub_date = datetime.now()

                articles.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'pub_date': pub_date
                })

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        return articles

    except Exception as e:
        print(f"Error scraping BBC Learning English: {e}")
        return []


def generate_feed(articles, output_path):
    """Generate RSS feed from articles"""

    fg = FeedGenerator()
    fg.title('BBC Learning English')
    fg.link(href='https://www.bbc.co.uk/learningenglish/english/', rel='alternate')
    fg.description('English language learning content from BBC')
    fg.language('en')

    for article in articles:
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.description(article['description'])
        fe.published(article['pub_date'])
        fe.guid(article['link'], permalink=True)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate RSS feed
    fg.rss_file(output_path, pretty=True)
    print(f"✓ Generated RSS feed: {output_path}")
    print(f"  Found {len(articles)} articles")


def main():
    """Main function"""
    print("Scraping BBC Learning English...")
    articles = scrape_bbc_learning()

    if articles:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'feeds', 'bbc_learning.xml')
        generate_feed(articles, output_path)
    else:
        print("⚠ No articles found")


if __name__ == '__main__':
    main()
