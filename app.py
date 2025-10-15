# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import traceback
from dotenv import load_dotenv
load_dotenv()

# Optional: try to import Groq — but allow fallback to mock
USE_MOCK = os.getenv("USE_MOCK", "0") == "1"
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = None
if not USE_MOCK:
    try:
        from groq import Groq
        if GROQ_KEY:
            client = Groq(api_key=GROQ_KEY)
        else:
            # If no key provided, fall back to mock
            USE_MOCK = True
    except Exception:
        # can't import groq -> fallback to mock
        USE_MOCK = True

app = FastAPI(title="HealBuddy - Symptom Checker (with mock fallback)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT,
            suggestion TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class SymptomInput(BaseModel):
    symptoms: str

@app.get("/")
def root():
    return {"message": "HealBuddy backend is running", "use_mock": USE_MOCK}

@app.post("/check")
def check(data: SymptomInput):
    try:
        symptoms = data.symptoms.strip()
        if not symptoms:
            raise HTTPException(status_code=400, detail="No symptoms provided")

        # If mock mode: return a stable canned response so frontend/demo works
        if USE_MOCK:
            suggestion = (
                "**(MOCK)** Disclaimer: Educational only.\n\n"
                f"Symptoms received: {symptoms}\n\n"
                "Possible conditions: Common viral infection, Seasonal flu (educational guess).\n"
                "Next steps: Rest, hydrate, monitor temperature, consult a doctor if worsening.\n"
            )
        else:
            # Real Groq call
            prompt = (
                f"You are a helpful healthcare assistant (educational only). "
                f"User symptoms: {symptoms}. List 2-3 possible conditions and safe next steps. "
                "Include an educational disclaimer that this is not medical advice."
            )
            # Use a currently supported model
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a medical assistant (educational only)."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Defensive extraction
            try:
                suggestion = resp.choices[0].message.content.strip()
            except Exception:
                suggestion = str(resp)

        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (symptoms, suggestion) VALUES (?, ?)", (symptoms, suggestion))
        conn.commit()
        conn.close()

        return {"suggestion": suggestion}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ BACKEND ERROR:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, symptoms, suggestion FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"history": [{"id": r[0], "symptoms": r[1], "suggestion": r[2]} for r in rows]}





# client = Groq(api_key="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")  