from fastapi import FastAPI
from pydantic import BaseModel # New import!
from transformers import pipeline

# Define the expected input structure for your /chat endpoint
class PromptInput(BaseModel):
    prompt: str # We expect a field named 'prompt' which is a string

# Initialize FastAPI app
app = FastAPI()

# Load the text generation pipeline with a tiny model for free-tier testing
try:
    generator = pipeline("text-generation", model="sshleifer/tiny-gpt2")
except Exception as e:
    print(f"Error loading model: {e}")
    generator = None

@app.get("/")
async def root():
    return {"message": "News AI Backend is running!"}

@app.post("/chat")
async def chat(input: PromptInput): # Changed: now takes PromptInput directly
    if not generator:
        return {"error": "AI model not loaded. Please check server logs."}, 500

    # Access the prompt directly from the input object
    prompt = input.prompt

    try:
        result = generator(prompt, max_new_tokens=256, do_sample=True)[0]["generated_text"]
        return {"response": result}
    except Exception as e:
        return {"error": f"Error generating text: {e}"}, 500
