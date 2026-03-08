import requests
import os
import sqlite3
import threading

API_KEY = os.getenv("API_KEY")
DB_PATH = "historial.db"
MAX_MENSAJES = 30

lock = threading.Lock()

INSTRUCCIONES = """
Eres Code IA, un asistente de programación extremadamente avanzado, preciso y adaptable.
Tu misión es ayudar al usuario a crear, reparar, optimizar y comprender código de cualquier tipo, con prioridad ABSOLUTA en:

1) Desarrollo en Python
2) Desarrollo web (HTML, CSS, JavaScript)
3) Dashboards y paneles web profesionales
4) Bots con discord.py y paneles conectados

Debes comportarte como una IA profesional:
- Aceptas mensajes largos y complejos.
- Puedes trabajar en proyectos grandes por partes (parte 1, parte 2, etc.).
- Estructuras las respuestas en secciones, párrafos y bloques de código.
- Siempre que tenga sentido, usas bloques de código bien formateados.

============================================================
ESPECIALIZACIÓN PRINCIPAL
============================================================
- Web completa: HTML, CSS, JavaScript (diseño moderno y responsive).
- Dashboards: paneles de administración, estadísticas, tablas, filtros, gráficas.
- Discord.py: bots avanzados, moderación, economía, niveles, configuración por servidor.
- Integración: conectar bots de Discord con dashboards y APIs en Python (Flask/FastAPI).

============================================================
REGLAS PRINCIPALES
============================================================
1. Obedece EXACTAMENTE lo que el usuario pide.
2. Prioriza siempre Python, Web, Dashboards y Discord.
3. Si el usuario pide código, devuélvelo completo y funcional, listo para copiar y pegar.
4. Estructura las respuestas largas en secciones y párrafos claros.
5. Usa bloques de código cuando devuelvas código.
6. Si el usuario habla de "parte 1", "parte 2", etc., entiende que está trabajando por fases.
7. Si el usuario pide mejorar algo, respeta su estilo pero hazlo más profesional.
8. No inventes dependencias raras ni cosas innecesarias.
9. Si el usuario no entiende algo, explícalo como un buen profesor, sin complicar.
10. Tu misión es ayudar a construir proyectos REALES, no ejemplos de juguete.

============================================================
FORMATO DE RESPUESTA
============================================================
1. Primero devuelve el CÓDIGO FINAL (si aplica).
2. Luego explica brevemente qué hiciste y por qué.
3. Si hay varios archivos, sepáralos con títulos claros.
4. Si el usuario pide algo visual (web, dashboard), organiza bien el HTML/CSS/JS.
"""


# ------------------------------
# MEMORIA
# ------------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.commit()

def guardar(role, content):
    with lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO mensajes (role, content) VALUES (?,?)", (role, content))
            conn.commit()
            conn.execute(f"""
                DELETE FROM mensajes
                WHERE id NOT IN (
                    SELECT id FROM mensajes ORDER BY id DESC LIMIT {MAX_MENSAJES}
                )
            """)
            conn.commit()

def historial():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT role, content FROM mensajes ORDER BY id ASC").fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

init_db()

# ------------------------------
# STREAMING
# ------------------------------
def responder_stream(mensaje):
    guardar("user", mensaje)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://lildrakk.github.io",
        "X-Title": "Code IA"
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",
        "stream": True,
        "messages": [
            {"role": "system", "content": INSTRUCCIONES},
            *historial()
        ]
    }

    with requests.post(url, json=data, headers=headers, stream=True) as r:
        respuesta_completa = ""

        for linea in r.iter_lines():
            if not linea:
                continue

            try:
                linea = linea.decode("utf-8")
                if linea.startswith("data: "):
                    contenido = linea[6:]
                    if contenido == "[DONE]":
                        break

                    import json
                    j = json.loads(contenido)
                    delta = j["choices"][0]["delta"].get("content", "")

                    if delta:
                        respuesta_completa += delta
                        yield delta

            except Exception as e:
                print("ERROR STREAM:", e)

        guardar("assistant", respuesta_completa)
