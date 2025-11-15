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

# Initialize OpenAI client - LAZY INITIALIZATION
client = None


def get_openai_client():
    """Get or create OpenAI client - initialized on first use"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = OpenAI(api_key=api_key)
    return client


@app.get("/ask")
def ask(question: str = Query(..., description="Natural language question")):
    """
    Handles a natural-language question about Aurora members
    and answers based on the data from the Aurora public API.
    """

    # Fetch messages from Aurora API
    try:
        response = requests.get(AURORA_API)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch Aurora API: {e}"}

    # Parse response safely
    try:
        data = response.json()
    except json.JSONDecodeError:
        try:
            data = json.loads(response.text)
        except Exception:
            return {"error": "Failed to parse Aurora API response as JSON."}

    # Extract messages list from the 'items' key
    if isinstance(data, dict) and "items" in data:
        data = data["items"]

    # Validate structure
    if not isinstance(data, list):
        return {"error": "Unexpected data format from Aurora API.", "raw": str(data)[:500]}

    # Create a text corpus from messages
    messages_text = "\n".join(
        [f"{m.get('user_name', 'Unknown')}: {m.get('message', '')}" for m in data]
    )

    # Build the LLM prompt
    prompt = f"""
You are an assistant that answers questions about Aurora members based on the following messages.

Messages:
{messages_text}

Question: {question}

Answer concisely and only based on the above messages.
If the information isn't available, say: "I could not find that information."
"""

    # Query the OpenAI API for the answer
    try:
        client_instance = get_openai_client()
        completion = client_instance.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        return {"error": f"OpenAI API error: {e}"}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Member QA System is running"}
