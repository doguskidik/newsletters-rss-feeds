# Newsletters RSS Feeds

Otomatik olarak çeşitli newsletter'ları RSS feed'e çeviren GitHub Actions tabanlı sistem.

## Nasıl Çalışır?

1. GitHub Actions her 6 saatte bir otomatik çalışır
2. Python scraper'lar siteleri tarar
3. RSS XML dosyaları güncellenir
4. Değişiklikler otomatik commit edilir
5. RSS reader'ınızdan raw GitHub URL ile okursunuz

## Mevcut Newsletter'lar

- **The Batch** - DeepLearning.AI'dan AI haberleri
- **BBC Learning English** - İngilizce öğrenim içeriği

## RSS Feed URL'leri

Feed'leri RSS reader'ınıza eklemek için şu URL'leri kullanın:

```
https://raw.githubusercontent.com/KULLANICI_ADIN/newsletters-rss-feeds/main/feeds/the_batch.xml
https://raw.githubusercontent.com/KULLANICI_ADIN/newsletters-rss-feeds/main/feeds/bbc_learning.xml
```

**NOT:** `KULLANICI_ADIN` kısmını kendi GitHub kullanıcı adınızla değiştirin!

## Kurulum

### 1. Repo'yu Fork/Clone Edin

```bash
git clone https://github.com/KULLANICI_ADIN/newsletters-rss-feeds.git
cd newsletters-rss-feeds
```

### 2. Yerel Test (Opsiyonel)

```bash
# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Tüm scraper'ları çalıştır
python run_all.py

# Veya tek bir scraper çalıştır
python scrapers/the_batch.py
```

### 3. GitHub'a Push Edin

```bash
git add .
git commit -m "Initial setup"
git push origin main
```

### 4. GitHub Actions'ı Etkinleştirin

- GitHub repo'nuza gidin
- **Settings** → **Actions** → **General**
- **Workflow permissions** altında:
  - ✅ **Read and write permissions** seçin
  - ✅ **Allow GitHub Actions to create and approve pull requests** işaretleyin
- **Save** butonuna tıklayın

### 5. İlk Çalıştırmayı Tetikleyin

- Repo'da **Actions** sekmesine gidin
- **Update RSS Feeds** workflow'unu seçin
- **Run workflow** butonuna tıklayın
- Birkaç dakika içinde `feeds/` klasöründe XML dosyaları oluşacak

## Yeni Newsletter Ekleme

### 1. Yeni Scraper Oluşturun

`scrapers/` klasöründe yeni bir Python dosyası oluşturun:

```python
#!/usr/bin/env python3
"""
Örnek Newsletter RSS Feed Generator
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import os


def scrape_newsletter():
    """Newsletter sayfasını scrape et"""
    url = "https://example.com/newsletter"

    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = []

    # HTML yapısına göre seçicileri ayarla
    for item in soup.find_all('article')[:20]:
        title = item.find('h2').get_text(strip=True)
        link = item.find('a')['href']
        description = item.find('p').get_text(strip=True)

        articles.append({
            'title': title,
            'link': link,
            'description': description,
            'pub_date': datetime.now()
        })

    return articles


def generate_feed(articles, output_path):
    """RSS feed oluştur"""
    fg = FeedGenerator()
    fg.title('Newsletter Başlığı')
    fg.link(href='https://example.com', rel='alternate')
    fg.description('Newsletter açıklaması')
    fg.language('en')

    for article in articles:
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.description(article['description'])
        fe.published(article['pub_date'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path, pretty=True)
    print(f"✓ Generated: {output_path}")


def main():
    articles = scrape_newsletter()
    if articles:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'feeds', 'example.xml')
        generate_feed(articles, output_path)


if __name__ == '__main__':
    main()
```

### 2. Test Edin

```bash
python scrapers/yeni_newsletter.py
```

### 3. Commit & Push

```bash
git add scrapers/yeni_newsletter.py
git commit -m "Add new newsletter scraper"
git push
```

GitHub Actions otomatik olarak yeni scraper'ı da çalıştıracak!

## Sık Sorulan Sorular

### Ücretli mi?

Hayır, tamamen ücretsiz! Public repo'da GitHub Actions sınırsız. Private repo'da ayda 2.000 dakika ücretsiz.

### Çalışma sıklığı nasıl değiştirilir?

`.github/workflows/update.yml` dosyasındaki `cron` değerini düzenleyin:

```yaml
schedule:
  - cron: '0 */3 * * *'  # Her 3 saatte bir
  - cron: '0 0 * * *'    # Günde bir kez (gece yarısı)
  - cron: '0 */12 * * *' # 12 saatte bir
```

### RSS feed'ler neden güncellenmiyor?

1. **Actions** sekmesinde hata var mı kontrol edin
2. Settings → Actions → Workflow permissions: "Read and write" olmalı
3. HTML selectors değişmiş olabilir, scraper kodunu güncellemelisiniz

### Daha fazla newsletter ekleyebilir miyim?

Elbette! `scrapers/` klasörüne istediğiniz kadar `.py` dosyası ekleyin, `run_all.py` hepsini otomatik çalıştırır.

### Site yapısı değişirse ne olur?

Scraper'ın HTML seçicilerini güncellemelisiniz. Sitenin HTML yapısını inceleyip `find()` ve `find_all()` parametrelerini ayarlayın.

## Proje Yapısı

```
newsletters-rss-feeds/
├── .github/
│   └── workflows/
│       └── update.yml          # GitHub Actions workflow
├── scrapers/
│   ├── the_batch.py           # The Batch scraper
│   ├── bbc_learning.py        # BBC Learning scraper
│   └── yeni_scraper.py        # Yeni scraper'larınız buraya
├── feeds/
│   ├── the_batch.xml          # Üretilen RSS feed'ler
│   ├── bbc_learning.xml
│   └── yeni_feed.xml
├── run_all.py                 # Tüm scraper'ları çalıştırır
├── requirements.txt           # Python bağımlılıkları
└── README.md
```

## Teknolojiler

- **Python 3.11**
- **BeautifulSoup4** - HTML parsing
- **feedgen** - RSS feed oluşturma
- **requests** - HTTP istekleri
- **GitHub Actions** - Otomatik çalıştırma

## Lisans

MIT License - Olshansk'ın yönteminden esinlenildi.

## Katkıda Bulunma

Yeni newsletter scraper'ları eklemek için pull request gönderin!
