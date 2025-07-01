from fastapi import FastAPI
from pydantic import BaseModel, Field
import os
import google.generativeai as genai

# Define the expected input structure for /chat (existing)
class PromptInput(BaseModel):
    prompt: str

# Define the expected input structure for /summarize_article (existing)
class ArticleInput(BaseModel):
    article_text: str
    summary_length: str = "3 sentences" # Optional: allows user to specify length

# Define the expected input structure for /generate_headline (NEW!)
class HeadlineInput(BaseModel):
    text_content: str = Field(..., description="The article text or summary to generate headlines for.")
    num_headlines: int = Field(3, ge=1, le=10, description="Number of headlines to generate (1-10).")
    headline_style: str = Field("neutral and informative", description="Style of headlines (e.g., 'clickbait', 'serious', 'humorous').")


# Initialize FastAPI app
app = FastAPI()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    genai = None
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest') # Back to Flash model

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

# NEW ENDPOINT: Generate headlines for text content
@app.post("/generate_headline")
async def generate_headline(input: HeadlineInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    content = input.text_content
    num_headlines = input.num_headlines
    headline_style = input.headline_style

    # Craft a precise prompt for headline generation
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
        generated_headlines = response.text.strip().split('\n') # Split into a list of strings
        # Clean up potential numbering and empty lines
        cleaned_headlines = [
            h.strip() for h in generated_headlines if h.strip() and not h.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.'))
        ]
        # Re-add numbering if the AI sometimes forgets, or if we want consistent format
        final_headlines = [f"{i+1}. {h}" for i, h in enumerate(cleaned_headlines[:num_headlines])]
        if not final_headlines and generated_headlines: # Fallback if cleaning was too aggressive
            final_headlines = [f"{i+1}. {h.strip()}" for i, h in enumerate(generated_headlines[:num_headlines])]


        return {"headlines": final_headlines}

    except Exception as e:
        print(f"Error calling Gemini API for headline generation: {e}")
        return {"error": f"Failed to generate headlines: {e}"}, 500
