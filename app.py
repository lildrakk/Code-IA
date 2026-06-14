import os
import uuid
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

# Cargar .env
load_dotenv()

app = FastAPI(title="Xtreme AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar instrucciones del sistema
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

class ChatRequest(BaseModel):
    prompt: str
    mode: str = "chat"   # chat / file / zip
    language: str | None = None

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

def llamar_al_modelo(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(GROQ_URL, json=data, headers=headers)
    result = response.json()

    # Manejo de errores
    if "choices" not in result:
        error_msg = result.get("error", {}).get("message", "Error desconocido en la API de Groq.")
        return f"Error al generar respuesta: {error_msg}"

    return result["choices"][0]["message"]["content"]

@app.post("/generate")
async def generate(req: ChatRequest):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUSUARIO:\n{req.prompt}\n\nIA:\n"
    generated = llamar_al_modelo(full_prompt)

    if req.mode == "chat":
        return {"type": "chat", "content": generated}

    # Generar archivo
    file_id = str(uuid.uuid4())
    ext = "py" if (req.language or "").lower() == "python" else "txt"
    filename = f"{file_id}.{ext}"

    os.makedirs("outputs", exist_ok=True)
    filepath = f"outputs/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(generated)

    return {
        "type": "file",
        "content": generated,
        "file_url": f"http://nc.lynxnodes.es:25677/outputs/{filename}",
        "filename": filename
    }

# Montar frontend al final
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=25677) 
