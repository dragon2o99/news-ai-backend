import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz # Import the pytz library for timezone handling

# --- Configuration for websites to scrape ---
# IMPORTANT: You MUST customize the 'selector' for each website.
# Use browser's 'Inspect Element' to find the correct CSS selector for headlines.
WEBSITE_CONFIGS = {
    "The Globe and Mail": {
        "url": "https://www.theglobeandmail.com/",
        "selector": "h3.c-card__title a, h2.c-story-block__title a, h2.c-feature-block__headline-text a"
    },
    "Toronto Sun": {
        "url": "https://torontosun.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a"
    },
    "National Post": {
        "url": "https://nationalpost.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a"
    },
    "CP24": {
        "url": "https://www.cp24.com/",
        "selector": "h2 a, h3 a, .c-posts-card__headline a, .c-list-card__headline a"
    },
    "Ottawa Citizen": {
        "url": "https://ottawacitizen.com/",
        "selector": "h3.article-card__title a, h2.entry-title a, .card-title a"
    },
    "Juno News": {
        "url": "https://junonews.com/",
        "selector": "h3 a, a[data-testid='post-title-link']"
    },
    "Rebel News": {
        "url": "https://www.rebelnews.com/news",
        "selector": "h2.headline a, h3 a, .post-title a, .article-title a"
    },
    "CBC News": {
        "url": "https://www.cbc.ca/news",
        "selector": "h3.gs-c-promo-heading__title a, h3.cbc-card__headline a, a.cbc-card__headline-link"
    }
}

def get_headlines(url, selector):
    """Fetches headlines from a given URL using the specified CSS selector."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = []
        for element in soup.select(selector):
            text = element.get_text(strip=True)
            link = element.get('href')
            if text and link:
                # Ensure the link is absolute
                if not link.startswith(('http://', 'https://')):
                    # Basic attempt to make relative URLs absolute.
                    # This might need more sophisticated handling for complex relative paths.
                    from urllib.parse import urljoin
                    link = urljoin(url, link)
                headlines.append({"title": text, "link": link})
        return headlines
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    """Main function to scrape headlines from configured websites."""
    print("--- Canadian News Headlines (Mississauga, ON Perspective) ---")

    # Define the Eastern Timezone for timestamping
    eastern_tz = pytz.timezone('America/New_York')
    current_time_et = datetime.now(eastern_tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    print(f"Current Time (ET): {current_time_et}\n")

    for site_name, config in WEBSITE_CONFIGS.items():
        print(f"--- {site_name} ---")
        headlines = get_headlines(config["url"], config["selector"])
        if headlines:
            # Displaying top 10 headlines, or fewer if not enough are found
            for i, headline in enumerate(headlines[:10]):
                print(f"{i+1}. {headline['title']} ({headline['link']})")
        else:
            print(f"No headlines found or an error occurred for {site_name}.")
        print("\n") # Add a newline for better readability between sites

if __name__ == "__main__":
    main()
