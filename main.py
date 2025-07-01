from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai

# Define the expected input structure for /chat (existing)
class PromptInput(BaseModel):
    prompt: str

# Define the expected input structure for /summarize_article (NEW!)
class ArticleInput(BaseModel):
    article_text: str
    summary_length: str = "3 sentences" # Optional: allows user to specify length

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

# NEW ENDPOINT: Summarize an article
@app.post("/summarize_article")
async def summarize_article(input: ArticleInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    article = input.article_text
    summary_length = input.summary_length

    # Craft a precise prompt for summarization
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
