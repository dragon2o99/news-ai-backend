from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai # New import!

# Define the expected input structure
class PromptInput(BaseModel):
    prompt: str

# Initialize FastAPI app
app = FastAPI()

# Configure Gemini API
# Get your Google API token from Render environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    # In a production app, you'd handle this more robustly
    genai = None # Disable Gemini features if key is missing
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Choose the Gemini model to use
    # For text generation, 'gemini-pro' is a good choice.
    # You can explore other models available via genai.list_models()
    model = genai.GenerativeModel('gemini-1.5-pro-latest') # Trying Gemini 1.5 Pro!
#model = genai.GenerativeModel('gemini-1.5-flash-latest') # Using an available model!

@app.get("/")
async def root():
    return {"message": "News AI Backend is running (using Google Gemini API)!"}

@app.post("/chat")
async def chat(input: PromptInput):
    if not genai or not GOOGLE_API_KEY:
        return {"error": "Google API key not configured."}, 500

    prompt = input.prompt

    try:
        # Generate content using Gemini
        response = model.generate_content(prompt)
        # The actual text is usually in response.text
        generated_text = response.text
        return {"response": generated_text}

    except Exception as e:
        # Catch any errors from the Gemini API call
        print(f"Error calling Gemini API: {e}")
        return {"error": f"Failed to get response from Gemini AI: {e}"}, 500
