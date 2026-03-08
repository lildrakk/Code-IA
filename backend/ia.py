import requests
import os
import sqlite3
import threading

# ============================
# CONFIGURACIÓN
# ============================

API_KEY = os.getenv("API_KEY")
DB_PATH = "historial.db"
MAX_MENSAJES = 30  # contexto reciente

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

# ============================
# BASE DE DATOS (MEMORIA)
# ============================

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def guardar_mensaje(role, content):
    with lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO mensajes (role, content) VALUES (?, ?)",
                (role, content)
            )
            conn.commit()

            # Limpiar mensajes viejos (mantener solo los últimos MAX_MENSAJES)
            conn.execute(f"""
                DELETE FROM mensajes
                WHERE id NOT IN (
                    SELECT id FROM mensajes ORDER BY id DESC LIMIT {MAX_MENSAJES}
                )
            """)
            conn.commit()

def cargar_historial():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT role, content FROM mensajes ORDER BY id ASC
        """).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

# Inicializar BD al arrancar
init_db()

# ============================
# FUNCIÓN PRINCIPAL
# ============================

def responder(mensaje: str) -> str:
    print("========== DEBUG ==========")
    print("API_KEY:", API_KEY)
    print("MENSAJE RECIBIDO:", mensaje[:500])
    print("===========================")

    # Guardar mensaje del usuario en la memoria
    guardar_mensaje("user", mensaje)

    # Cargar historial reciente
    historial = cargar_historial()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://lildrakk.github.io",
        "X-Title": "Code IA"
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [
            {"role": "system", "content": INSTRUCCIONES},
            *historial
        ]
    }

    try:
        resp = requests.post(url, json=data, headers=headers, timeout=90)

        if resp.status_code != 200:
            print("ERROR OPENROUTER:", resp.status_code, resp.text)
            return f"⚠️ Error del servidor ({resp.status_code})."

        j = resp.json()
        contenido = j.get("choices", [{}])[0].get("message", {}).get("content")

        if not contenido:
            print("ERROR: JSON vacío:", j)
            return "⚠️ No pude generar una respuesta válida."

        # Guardar respuesta de la IA en la memoria
        guardar_mensaje("assistant", contenido)

        print("RESPUESTA (preview):", contenido[:500])
        return contenido

    except requests.exceptions.Timeout:
        print("ERROR: Timeout")
        return "⚠️ La IA tardó demasiado en responder. Prueba a pedirlo por partes."

    except Exception as e:
        print("ERROR INESPERADO:", e)
        return "⚠️ Error inesperado procesando tu mensaje."
