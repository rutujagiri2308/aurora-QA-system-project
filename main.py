from fastapi import FastAPI, Query
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

app = FastAPI(title="Aurora QA API", version="1.0")

# Aurora public API endpoint 
AURORA_API = "https://november7-730026606190.europe-west1.run.app/messages"

# Initialize OpenAI client 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/ask")
def ask(question: str = Query(..., description="Natural language question about Aurora members")):
    """
    Handles a natural-language question about Aurora members
    and answers based on the data from the Aurora public API.
    """
    # Fetch messages from Aurora API
    try:
        response = requests.get(AURORA_API)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"error": f"Failed to fetch Aurora API: {str(e)}"}

    # Prepare text context from fetched messages
    try:
        messages_text = "\n".join([
            f"{msg.get('user_name', 'Unknown')}: {msg.get('message', '')}"
            for msg in data.get("items", [])
        ])
    except Exception:
        return {"error": "Unexpected data format from Aurora API."}

    # Build the LLM prompt
    prompt = f"""
    You are a helpful assistant answering questions about Aurora members.
    The following are recent messages from members:
    {messages_text}

    Question: {question}

    Please provide a concise, factual answer using only the information from the messages.
    """

    # Generate the answer using OpenAI 
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # efficient and accurate for Q&A
            messages=[
                {"role": "system", "content": "You are an intelligent assistant trained to extract relevant facts from user messages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200,
        )
        answer = completion.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}


@app.get("/health")
def health():
    return {"status": "ok"}
