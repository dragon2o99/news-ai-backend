import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from urllib.parse import urljoin
import feedparser # Import the feedparser library

# --- Configuration for websites to scrape ---
# IMPORTANT: You MUST customize the 'selector' for each website if using direct scraping.
# For RSS feeds, you provide the 'rss_url'.
WEBSITE_CONFIGS = {
    "The Globe and Mail": {
        "url": "https://www.theglobeandmail.com/",
        "selector": "h3.c-card__title a, h2.c-story-block__title a, h2.c-feature-block__headline-text a",
        # Find their RSS feed if available. Many news sites have them.
        "rss_url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/"
        # I'll leave this commented out as you'll need to find the exact RSS URL.
    },
     "The Star": {
        "url": "https://thestar.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a",
        # Toronto Star RSS:
        "rss_url": "https://www.thestar.com/search/?f=rss&t=article&bl=2827101&l=20" # Common RSS feed path
    },
    "Toronto Sun": {
        "url": "https://torontosun.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a",
        # Toronto Sun RSS:
        "rss_url": "https://torontosun.com/feed" # Common RSS feed path
    },
    "National Post": {
        "url": "https://nationalpost.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a",
        # National Post RSS:
        "rss_url": "https://nationalpost.com/feed" # Common RSS feed path
    },
    "CP24": {
        "url": "https://www.cp24.com/",
        "selector": "h2 a, h3 a, .c-posts-card__headline a, .c-list-card__headline a",
        # CP24 has specific RSS feeds, e.g., for Toronto News:
        "rss_url": "https://www.cp24.com/polopoly_fs/1.3789512!/menu/generic.xml"
    },
    "Ottawa Citizen": {
        "url": "https://ottawacitizen.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a",
        # Ottawa Citizen RSS:
        "rss_url": "https://ottawacitizen.com/feed" # Common RSS feed path
    },
    "Juno News": { # This one timed out, so RSS is a good candidate if available
        "url": "https://junonews.com/",
        "selector": "h3 a, a[data-testid='post-title-link']",
        "rss_url": "https://www.junonews.com/feed"
        
    },
    "Rebel News": {
        "url": "https://www.rebelnews.com/news",
        "selector": "h2.headline a, h3 a, .post-title a, .article-title a",
        # Rebel News RSS:
        "rss_url": "https://www.rebelnews.com/feed" # Common RSS feed path
    },
    "CBC News": {
        "url": "https://www.cbc.ca/news",
        "selector": "h3.gs-c-promo-heading__title a, h3.cbc-card__headline a, a.cbc-card__headline-link",
        # CBC News has regional and topic-specific feeds. General news:
        "rss_url": "https://www.cbc.ca/cmlink/rss-topstories"
    }
}

# Add a User-Agent header to mimic a web browser for direct scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_headlines_from_rss(rss_url):
    """Fetches headlines from an RSS feed."""
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo: # Check for parsing errors
            print(f"Error parsing RSS feed {rss_url}: {feed.bozo_exception}")
            return []

        headlines = []
        for entry in feed.entries:
            title = entry.get('title', 'No Title').strip()
            link = entry.get('link', 'No Link').strip()
            if title and link:
                headlines.append({"title": title, "link": link})
        return headlines
    except Exception as e:
        print(f"Error fetching RSS feed {rss_url}: {e}")
        return []

def get_headlines_from_scrape(url, selector):
    """Fetches headlines from a given URL using the specified CSS selector (direct scraping)."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15) # Increased timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = []
        for element in soup.select(selector):
            text = element.get_text(strip=True)
            link = element.get('href')
            if text and link:
                # Ensure the link is absolute
                if not link.startswith(('http://', 'https://')):
                    link = urljoin(url, link)
                headlines.append({"title": text, "link": link})
        return headlines
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    """Main function to get headlines from configured websites, prioritizing RSS."""
    print("--- Canadian News Headlines (Mississauga, ON Perspective) ---")

    eastern_tz = pytz.timezone('America/New_York')
    current_time_et = datetime.now(eastern_tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    print(f"Current Time (ET): {current_time_et}\n")

    for site_name, config in WEBSITE_CONFIGS.items():
        print(f"--- {site_name} ---")
        headlines = []

        if "rss_url" in config and config["rss_url"]:
            print(f"Attempting to fetch from RSS: {config['rss_url']}")
            headlines = get_headlines_from_rss(config["rss_url"])
            if not headlines:
                print(f"RSS feed for {site_name} returned no headlines or failed. Falling back to direct scraping.")
                headlines = get_headlines_from_scrape(config["url"], config["selector"])
        else:
            print(f"No RSS URL configured for {site_name}. Proceeding with direct scraping.")
            headlines = get_headlines_from_scrape(config["url"], config["selector"])

        if headlines:
            for i, headline in enumerate(headlines[:10]):
                print(f"{i+1}. {headline['title']} ({headline['link']})")
        else:
            print(f"No headlines found or an error occurred for {site_name}.")
        print("\n")

if __name__ == "__main__":
    main()
