from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import google.generativeai as genai
import httpx # NEW IMPORT
from bs4 import BeautifulSoup # NEW IMPORT
import asyncio # NEW IMPORT

# Define the expected input structure for /chat (existing)
class PromptInput(BaseModel):
    prompt: str

# Define the expected input structure for /summarize_article (existing)
class ArticleInput(BaseModel):
    article_text: str
    summary_length: str = "3 sentences" # Optional: allows user to specify length

# Define the expected input structure for /generate_headline (existing)
class HeadlineInput(BaseModel):
    text_content: str = Field(..., description="The article text or summary to generate headlines for.")
    num_headlines: int = Field(3, ge=1, le=10, description="Number of headlines to generate (1-10).")
    headline_style: str = Field("neutral and informative", description="Style of headlines (e.g., 'clickbait', 'serious', 'humorous').")


# Initialize FastAPI app
app = FastAPI()

# --- CORS CONFIGURATION ---
origins = [
    "*" # Allows requests from any origin. For production, specify your Vercel URL here!
    # Example for production: "https://your-frontend-name.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END CORS CONFIGURATION ---

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    genai = None
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- NEW: Configuration for websites to scrape ---
# IMPORTANT: You MUST customize these with actual URLs and their
# specific CSS selectors for headlines.
# To find selectors:
# 1. Go to the news website in Chrome/Firefox.
# 2. Right-click on a headline you want to scrape and select "Inspect" (or "Inspect Element").
# 3. In the developer tools, find the HTML tag (e.g., h2, div, a) that contains the headline text.
# 4. Look for a unique class name (e.g., class="headline-title") or an ID.
# 5. Your selector might look like: "h2.headline-title a" (for an <a> tag inside an <h2> with that class)
#    or just "a.story-link" if the link itself has a specific class.
#    If headlines are in multiple elements, you might need multiple selectors separated by commas: "h2.headline-class a, div.other-headline-class span"
WEBSITE_CONFIGS = {
    "BBC News (Example)": {
        "url": "https://www.bbc.com/news",
        "selector": "h3.gs-c-promo-heading__title a, h3.nw-c-promo-heading__title a"
    },
    "CNN (Example)": {
        "url": "https://edition.cnn.com/",
        "selector": "h2.card__headline a, span.container__headline-text"
    },
    "NY Times (Example)": {
        "url": "https://www.nytimes.com/",
        "selector": "h3.css-1j68v0b e1hr93s50, h2.css-1e8yqj5 e1h9rw260" # These selectors often change, so verify!
    },
    # Add 2 more real news sites here with their specific selectors.
    # Remember to inspect each site's HTML to get the correct selector.
    "The Guardian (Example)": {
        "url": "https://www.theguardian.com/uk",
        "selector": "h3.fc-item__title a"
    },
    "Reuters (Example)": {
        "url": "https://www.reuters.com/",
        "selector": "h3.media-story-card__title a"
    }
}


# --- NEW ASYNC SCRAPING FUNCTIONS ---
async def fetch_url(url: str) -> str | None:
    # User-Agent to mimic a browser, sometimes helps with basic anti-scraping
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout slightly
        try:
            response = await client.get(url, follow_redirects=True, headers=headers)
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            return response.text
        except httpx.RequestError as e:
            print(f"HTTP request failed for {url}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP status error for {url}: {e.response.status_code} - {e.response.text}")
            return None

def parse_headlines(html_content: str, selector: str, limit: int = 10) -> list[str]:
    soup = BeautifulSoup(html_content, 'html.parser')
    headlines = []
    # Find all elements matching the selector and extract text
    for i, tag in enumerate(soup.select(selector)):
        if i >= limit:
            break # Stop after reaching the limit
        text = tag.get_text(strip=True)
        # Basic cleaning: remove extra whitespace, common navigation text, ensure not empty
        cleaned_text = ' '.join(text.split()).replace('  ', ' ')
        if cleaned_text and len(cleaned_text) > 10: # Ensure it's not empty and reasonable length
            headlines.append(cleaned_text)
    return headlines

async def scrape_website(site_name: str, config: dict) -> dict:
    url = config["url"]
    selector = config["selector"]
    print(f"Attempting to scrape: {site_name} from {url}")
    html_content = await fetch_url(url)
    if html_content:
        headlines = parse_headlines(html_content, selector)
        print(f"Scraped {len(headlines)} headlines from {site_name}")
        return {"site": site_name, "url": url, "headlines": headlines}
    else:
        print(f"Failed to scrape {site_name}")
        return {"site": site_name, "url": url, "headlines": [], "error": "Failed to fetch or parse"}

# --- END NEW ASYNC SCRAPING FUNCTIONS ---

@app.get("/")
async def root():
    return {"message": "News AI Backend is running (using Google Gemini API)!"}

@app.post("/chat")
async def chat(input: PromptInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    prompt = input.prompt

    try:
        response = model.generate_content(prompt)
        generated_text = response.text
        return {"response": generated_text}

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {"error": f"Failed to get response from Gemini AI: {e}"}, 500

@app.post("/summarize_article")
async def summarize_article(input: ArticleInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    article = input.article_text
    summary_length = input.summary_length

    prompt = f"""Summarize the following news article into {summary_length}.
    Ensure the summary is concise, captures the main points, and is suitable for a news brief.

    Article:
    ---
    {article}
    ---
    Summary:
    """

    try:
        response = model.generate_content(prompt)
        generated_summary = response.text
        return {"summary": generated_summary}

    except Exception as e:
        print(f"Error calling Gemini API for summarization: {e}")
        return {"error": f"Failed to summarize article: {e}"}, 500

@app.post("/generate_headline")
async def generate_headline(input: HeadlineInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    content = input.text_content
    num_headlines = input.num_headlines
    headline_style = input.headline_style

    prompt = f"""Generate {num_headlines} distinct news headlines for the following text.
    The headlines should be {headline_style}.
    Present each headline on a new line, prefixed with a number (e.g., "1. Headline").

    Text:
    ---
    {content}
    ---
    Headlines:
    """

    try:
        response = model.generate_content(prompt)
        generated_headlines = response.text.strip().split('\n')
        cleaned_headlines = [
            h.strip() for h in generated_headlines if h.strip() and not h.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.'))
        ]
        final_headlines = [f"{i+1}. {h}" for i, h in enumerate(cleaned_headlines[:num_headlines])]
        if not final_headlines and generated_headlines:
            final_headlines = [f"{i+1}. {h.strip()}" for i, h in enumerate(generated_headlines[:num_headlines])]

        return {"headlines": final_headlines}

    except Exception as e:
        print(f"Error calling Gemini API for headline generation: {e}")
        return {"error": f"Failed to generate headlines: {e}"}, 500

# NEW ENDPOINT: Crawl, Analyze, and Post Headlines
@app.post("/crawl_and_analyze")
async def crawl_and_analyze():
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    # Step 1: Scrape headlines concurrently from all configured websites
    scraped_data = await asyncio.gather(
        *[scrape_website(name, config) for name, config in WEBSITE_CONFIGS.items()]
    )

    all_headlines_raw = []
    for site_data in scraped_data:
        all_headlines_raw.extend(site_data["headlines"])

    if not all_headlines_raw:
        return {"message": "No headlines were scraped from any of the configured sites.", "scraped_details": scraped_data}

    # Step 2: Prepare headlines for AI analysis
    # Combine all headlines into a single string for the AI prompt
    headlines_for_ai = "\n".join([f"- {h}" for h in all_headlines_raw])

    # Step 3: Craft a detailed prompt for AI analysis
    ai_analysis_prompt = f"""
    Analyze the following collection of news headlines from various sources. Provide your analysis in the following structured format. If a category or theme is not applicable, state 'N/A'.

    ---
    Overall Dominant Theme:
    [One concise sentence (max 25 words) describing the main overarching topic or trend across ALL headlines, considering their collective significance.]

    Categorized Headlines:
    [For EACH headline, assign ONE primary category from (Politics, Sports, Tech, General News, Other) and ONE sentiment (Positive, Negative, Neutral). Use the exact format:
    - [Category]: [Sentiment]: [Headline Text]
    Example:
    - Politics: Neutral: New bill passes parliament.
    - Sports: Positive: Local team wins championship.
    - Tech: Neutral: Company unveils new gadget.
    - General News: Negative: Economic downturn continues.
    ]

    Common Themes/Keywords:
    [List 3 to 5 common themes or keywords that frequently appear across these headlines, separated by commas. Focus on high-level concepts.]
    ---

    News Headlines for Analysis:
    {headlines_for_ai}
    """

    try:
        ai_response = model.generate_content(ai_analysis_prompt)
        analysis_text = ai_response.text.strip()

        # For now, we'll return the raw text analysis from Gemini.
        # Parsing this into structured JSON on the backend would be the next step for programmatic use.

        return {
            "message": "Successfully crawled and analyzed headlines.",
            "scraped_details": scraped_data, # Shows what was scraped from each site
            "ai_analysis": analysis_text # Gemini's raw text analysis
        }

    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return {"error": f"Failed to analyze headlines: {e}"}, 500
