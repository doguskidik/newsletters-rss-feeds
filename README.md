# Newsletters RSS Feeds

Automatically converts newsletters into RSS feeds using GitHub Actions and GitHub Pages. Scrapers run every 6 hours and publish updated XML feeds.

## Available Feeds

| Newsletter | Feed URL |
|---|---|
| **The Batch** (DeepLearning.AI) | `https://doguskidik.github.io/newsletters-rss-feeds/feeds/the_batch.xml` |

## How It Works

1. GitHub Actions runs scrapers every 6 hours
2. Scrapers fetch content from source websites
3. RSS XML files are generated and committed
4. Feeds are served via GitHub Pages

## Fork & Deploy

You can fork this repo and get your own hosted feeds — **no configuration needed**. The GitHub Pages URL is auto-detected from `GITHUB_REPOSITORY` at runtime.

### 1. Fork the repository

Click **Fork** on GitHub.

### 2. Enable GitHub Pages

Go to your fork → **Settings** → **Pages** → Source: `main` branch, `/ (root)` → **Save**.

### 3. Enable Actions write permission

**Settings** → **Actions** → **General** → **Workflow permissions** → select **Read and write permissions** → **Save**.

### 4. Run the workflow

**Actions** → **Update RSS Feeds** → **Run workflow**.

Your feeds will be available at:
```
https://<your-username>.github.io/newsletters-rss-feeds/feeds/the_batch.xml
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all scrapers
python run_all.py

# Run a single scraper
python scrapers/the_batch.py
```

## Adding a New Scraper

1. Create a new file in `scrapers/` (e.g. `scrapers/my_newsletter.py`)
2. Implement a `main()` function that writes to `feeds/my_newsletter.xml`
3. `run_all.py` automatically discovers and runs all `*.py` files in `scrapers/`

Minimal scraper template:

```python
import os
from feedgen.feed import FeedGenerator

def main():
    fg = FeedGenerator()
    fg.title("My Newsletter")
    fg.link(href="https://example.com", rel="alternate")
    fg.description("My newsletter description")
    fg.language("en")

    # ... fetch and add entries ...

    output_path = os.path.join(os.path.dirname(__file__), "..", "feeds", "my_newsletter.xml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path, pretty=True)

if __name__ == "__main__":
    main()
```

## Project Structure

```
newsletters-rss-feeds/
├── .github/workflows/update.yml   # Runs every 6 hours
├── scrapers/
│   ├── the_batch.py               # DeepLearning.AI – The Batch
│   └── bbc_learning.py            # BBC Learning English (WIP)
├── feeds/
│   └── the_batch.xml              # Generated RSS feeds
├── run_all.py                     # Discovers and runs all scrapers
└── requirements.txt
```

## Dependencies

- `requests` — HTTP
- `beautifulsoup4` — HTML parsing
- `feedgen` — RSS generation
- `lxml` — XML post-processing
