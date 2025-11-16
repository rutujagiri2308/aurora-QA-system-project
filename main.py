from fastapi import FastAPI, Query
import requests
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Aurora Member QA System 🚀",
    description="""
A natural language **Question-Answering API** that fetches live data from Aurora's public API 
and uses **OpenAI GPT-4o-mini** to respond to member-related queries.

### Key Features
- 🔗 Real-time Aurora data
- 🧠 GPT-powered answers
- 🧩 Clean REST endpoint `/ask`
- 🌐 Deployed on Railway
    """,
    version="1.0.0",
    contact={
        "name": "Rutuja Giri",
        "url": "https://github.com/rutujagiri2308/aurora-QA-system-project",
        "email": "rutujagiri2308@gmail.com",
    },
)

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
        # Initialize without passing problematic parameters
        try:
            client = OpenAI(api_key=api_key)
        except TypeError as e:
            # If proxies parameter error, try alternative initialization
            if "proxies" in str(e):
                import httpx
                # Create custom HTTP client without proxies
                http_client = httpx.Client(
                    timeout=30.0,
                    limits=httpx.Limits(max_keepalive_connections=5)
                )
                client = OpenAI(api_key=api_key, http_client=http_client)
            else:
                raise
    return client


@app.get("/ask")
def ask(question: str = Query(..., description="Natural language question")):
    """
    Handles a natural-language question about Aurora members
    and answers based on the data from the Aurora public API.
    """

    # Fetch messages from Aurora API
    try:
        response = requests.get(AURORA_API, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch Aurora API: {e}"}

    try:
        data = response.json()
    except json.JSONDecodeError:
        try:
            data = json.loads(response.text)
        except Exception:
            return {"error": "Failed to parse Aurora API response as JSON."}

    if isinstance(data, dict) and "items" in data:
        data = data["items"]

    if not isinstance(data, list):
        return {"error": "Unexpected data format"}

    messages_text = "\n".join(
        [f"{m.get('user_name', 'Unknown')}: {m.get('message', '')}" for m in data]
    )

    #Build the LLM prompt
    prompt = f"""
You are an assistant that answers questions about Aurora members based on the following messages.

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
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        answer = completion.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        return {"error": f"OpenAI error: {str(e)}"}

# Too check health
@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Member QA System is running"}
