from fastapi import FastAPI, Request
from transformers import pipeline

# Initialize FastAPI app
app = FastAPI()

# Load the text generation pipeline with a small, efficient model
# Mistral-7B-Instruct-v0.1 is a good choice for this purpose
# Note: This will download the model the first time it runs on Render.
try:
   generator = pipeline("text-generation", model="sshleifer/tiny-gpt2")
except Exception as e:
    print(f"Error loading model: {e}")
    # Fallback or exit if model loading fails
    generator = None # Or handle more gracefully

@app.get("/")
async def root():
    return {"message": "News AI Backend is running!"}

@app.post("/chat")
async def chat(request: Request):
    if not generator:
        return {"error": "AI model not loaded. Please check server logs."}, 500

    data = await request.json()
    prompt = data.get("prompt", "Summarize this news article.")

    # You can add more complex prompt engineering here later
    # For now, it's a simple text generation based on the prompt

    try:
        # Generate text
        # max_new_tokens controls the length of the generated response
        # do_sample=True allows for more creative, less repetitive output
        result = generator(prompt, max_new_tokens=256, do_sample=True)[0]["generated_text"]
        return {"response": result}
    except Exception as e:
        return {"error": f"Error generating text: {e}"}, 500
