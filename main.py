from fastapi import FastAPI, Query
import requests
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Aurora QA API", version="1.0")

AURORA_API = "https://november7-730026606190.europe-west1.run.app/messages"

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.get("/ask")
def ask(question: str = Query(..., description="Natural language question about Aurora members")):
    """
    Handles a natural-language question about Aurora members and answers
    based on the data from the Aurora public API.
    """
    try:
        response = requests.get(AURORA_API)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"error": f"Failed to fetch Aurora API: {str(e)}"}

    # Prepare message data for LLM
    try:
        messages_text = "\n".join([
            f"{msg.get('user_name', 'Unknown')}: {msg.get('message', '')}"
            for msg in data.get("items", [])
        ])
    except Exception:
        return {"error": "Unexpected data format from Aurora API."}

    # Query the model
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the following user messages."},
                {"role": "user", "content": f"Messages:\n{messages_text}\n\nQuestion: {question}"}
            ],
            max_tokens=150
        )
        answer = completion.choices[0].message["content"].strip()
        return {"answer": answer}
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}


@app.get("/health")
def health():
    return {"status": "ok"}
