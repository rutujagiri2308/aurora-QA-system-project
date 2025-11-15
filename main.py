from fastapi import FastAPI, Query
import requests
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Aurora public API endpoint
AURORA_API = "https://november7-730026606190.europe-west1.run.app/messages"

# CRITICAL FIX: Don't initialize at import time
client = None


def get_openai_client():
    """Initialize client only when needed"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
    return client


@app.get("/ask")
def ask(question: str = Query(..., description="Natural language question")):
    """Handles natural language questions about Aurora members"""
    try:
        response = requests.get(AURORA_API)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch Aurora API: {e}"}

    try:
        data = response.json()
    except json.JSONDecodeError:
        try:
            data = json.loads(response.text)
        except Exception:
            return {"error": "Failed to parse Aurora API response"}

    if isinstance(data, dict) and "items" in data:
        data = data["items"]

    if not isinstance(data, list):
        return {"error": "Unexpected data format"}

    messages_text = "\n".join(
        [f"{m.get('user_name', 'Unknown')}: {m.get('message', '')}" for m in data]
    )

    prompt = f"""Answer questions about Aurora members based on this data:

{messages_text}

Question: {question}

Answer concisely from the data. If not found, say "Information not available"."""

    try:
        client_instance = get_openai_client()
        completion = client_instance.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        return {"error": f"OpenAI error: {e}"}


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok"}
