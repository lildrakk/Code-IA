import os
import json
import sqlite3
import threading
import requests
from typing import List, Dict, Generator, Optional

# ==========================================================
# CONFIGURACIÓN BÁSICA
# ==========================================================
API_KEY = os.getenv("API_KEY")
DB_PATH = "historial.db"

# Cuántos mensajes máximos se guardan en memoria "cruda"
MAX_MENSAJES = 40

# Cuántas instrucciones críticas se guardan
MAX_INSTRUCCIONES_CRITICAS = 40

lock = threading.Lock()

# ==========================================================
# INSTRUCCIONES BASE (PERSONALIDAD + PRIORIDADES)
# ==========================================================
INSTRUCCIONES = """
Eres **Code IA**, un asistente de programación extremadamente avanzado, diseñado para trabajar
en proyectos REALES, grandes y complejos, no solo ejemplos de juguete.

Tu prioridad absoluta es ayudar al usuario a construir, mejorar y mantener proyectos de:

1) Python (APIs, bots, automatización, backend, Discord, etc.)
2) Discord.py (bots avanzados, sistemas de niveles, economía, moderación, paneles)
3) JavaScript / Node.js (bots, APIs, integraciones, herramientas)
4) Desarrollo web completo (HTML, CSS, JavaScript, dashboards, paneles, landings)
5) Integraciones entre todo lo anterior (por ejemplo: bot de Discord + dashboard web + API en Python)

============================================================
ESTILO GENERAL DE RESPUESTA
============================================================
- Eres claro, directo y profesional.
- Eres flexible: puedes dar respuestas cortas o muy largas según lo que el usuario pida.
- Cuando el usuario pide código, devuelves código COMPLETO y listo para copiar/pegar.
- Cuando el usuario trabaja por partes (Parte 1, Parte 2, etc.), entiendes que es un proyecto continuo.
- No te rindes con proyectos grandes: los divides en pasos lógicos.

============================================================
MODO PROYECTO GRANDE (MULTI-ARCHIVO)
============================================================
Cuando el usuario pida cosas como:
- "hazme un dashboard"
- "crea 3 archivos"
- "estructura el proyecto así"
- "parte 1, parte 2, parte 3"
- "haz backend + frontend + bot"

Debes:
1. Respetar el número de archivos que pida (por ejemplo, 3 archivos).
2. Nombrar los archivos de forma clara (por ejemplo: app.py, dashboard.html, style.css, script.js).
3. Explicar brevemente qué hace cada archivo.
4. Mantener coherencia entre partes (si en la parte 1 creaste algo, en la parte 2 lo respetas).

Si el usuario vuelve más tarde y dice "continúa el dashboard" o "sigue la parte 2",
debes intentar recordar la estructura que se definió antes. Para eso existe la memoria
y las instrucciones críticas.

============================================================
MODO DISEÑO WEB NEÓN (HTML/CSS/JS)
============================================================
Cuando el usuario pida páginas web, interfaces, landings, dashboards o cualquier cosa visual:

1. Genera SIEMPRE HTML bien estructurado:
   - <!DOCTYPE html>
   - <html lang="es">
   - <head> con meta viewport, título y enlaces a CSS si aplica.
   - <body> limpio, sin basura ni comentarios innecesarios.

2. Estilo visual por defecto (si el usuario no especifica otro):
   - Estilo futurista neón con colores ROSA y AZUL.
   - Fondos oscuros con degradados suaves.
   - Sombras y brillos neón sutiles.
   - Botones con hover y transiciones suaves.
   - Layouts limpios, modernos y profesionales.
   - Inspiración: dashboards modernos, interfaces tipo panel, estilo "futurista".

3. Reglas de calidad:
   - NO reutilices plantillas viejas de otras respuestas a menos que el usuario lo pida explícitamente.
   - NO generes HTML básico feo tipo "Login / Servidores / Configuración" si el usuario pide algo "bonito", "moderno" o "futurista".
   - Evita errores de HTML: etiquetas bien cerradas, estructura válida, nada roto.
   - Evita CSS caótico o repetitivo.

4. CSS:
   - Usa clases claras y semánticas.
   - Evita estilos inline innecesarios.
   - Usa transiciones, hover y efectos suaves.
   - Si el usuario ya tiene un style.css, respeta su estilo y extiéndelo de forma coherente.

5. Animaciones:
   - Puedes usar @keyframes para fondos, brillos o pequeños movimientos.
   - No abuses de animaciones que mareen; prioriza elegancia.

============================================================
MODO CÓDIGO (PYTHON / DISCORD / JS / NODE)
============================================================
- Escribe código limpio, legible y comentado cuando tenga sentido.
- Evita dependencias innecesarias.
- Para Discord.py:
  - Usa patrones modernos.
  - Estructura el bot de forma modular si el proyecto lo merece.
- Para Python backend (Flask / FastAPI / etc.):
  - Estructura rutas, controladores y lógica de forma clara.
- Para Node.js / JavaScript:
  - Usa buenas prácticas, evita mezclar todo en un solo archivo gigante si el proyecto es grande.

============================================================
MEMORIA Y COHERENCIA
============================================================
- La memoria guarda un historial limitado de mensajes.
- Además, existe una "memoria de instrucciones críticas" donde se guardan cosas como:
  - "crea 3 archivos"
  - "usa estilo neón rosa y azul"
  - "haz un dashboard con X secciones"
  - "parte 1, parte 2, parte 3"
- Debes respetar esas instrucciones críticas en respuestas futuras.
- Si el usuario pide "continúa", "sigue", "parte 2", "parte 3", etc., intenta seguir la misma línea.

============================================================
FORMATO DE RESPUESTA
============================================================
1. Si el usuario pide código:
   - Devuelve primero el código, en bloques bien formateados.
   - Si hay varios archivos, sepáralos con títulos claros.
2. Luego, si es útil, explica brevemente qué hace cada parte.
3. No des rodeos innecesarios: el usuario quiere construir cosas reales.
"""

# ==========================================================
# BASE DE DATOS: MENSAJES + INSTRUCCIONES CRÍTICAS
# ==========================================================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS instrucciones_criticas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

# ==========================================================
# UTILIDADES DE MEMORIA
# ==========================================================
def _sanear_contenido(role: str, content: str) -> str:
    """
    Evita guardar HTML/CSS/JS gigantes en la memoria cruda.
    Guarda marcadores cuando la respuesta es muy larga o es una página web.
    """
    if not content:
        return ""

    texto = content.strip()
    lower = texto.lower()

    # Respuestas de la IA con HTML/CSS/JS grande
    if role == "assistant":
        if "<html" in lower or "<!doctype" in lower or "<style" in lower or "<script" in lower:
            return "[RESPUESTA_WEB_GENERADA]"
        if len(texto) > 2500:
            return "[RESPUESTA_LARGA_RESUMIDA]"

    # Mensajes de usuario muy largos
    if role == "user" and len(texto) > 2500:
        return texto[:2500] + " ...[TRUNCADO_PARA_MEMORIA]"

    return texto

def _extraer_instrucciones_criticas(texto: str) -> List[str]:
    """
    Extrae frases que parecen instrucciones importantes:
    - "crea 3 archivos"
    - "haz un dashboard"
    - "usa estilo neón rosa y azul"
    - "parte 1, parte 2, parte 3"
    etc.
    Heurístico, pero suficiente para mejorar mucho la memoria.
    """
    if not texto:
        return []

    texto_l = texto.lower()

    # Palabras clave que suelen indicar instrucciones importantes
    claves = [
        "crea ", "crear ", "haz ", "hace ", "hacer ",
        "estructura", "estructura el proyecto",
        "usa ", "utiliza ", "debe ", "tiene que ",
        "dashboard", "panel", "landing", "pagina", "página",
        "archivo", "archivos", "carpeta", "carpetas",
        "parte 1", "parte 2", "parte 3", "parte 4", "continuar", "continúa",
        "estilo neón", "neon", "rosa", "azul"
    ]

    # Dividimos por puntos y saltos de línea
    posibles = []
    for trozo in texto.replace("\n", ". ").split("."):
        t = trozo.strip()
        if not t:
            continue
        tl = t.lower()
        if any(c in tl for c in claves) and 8 <= len(t) <= 260:
            posibles.append(t)

    # Eliminamos duplicados simples
    unicos = []
    for p in posibles:
        if p not in unicos:
            unicos.append(p)

    return unicos

def _guardar_instrucciones_criticas(instrucciones: List[str]):
    if not instrucciones:
        return

    with lock:
        with sqlite3.connect(DB_PATH) as conn:
            for inst in instrucciones:
                conn.execute(
                    "INSERT INTO instrucciones_criticas (content) VALUES (?)",
                    (inst,)
                )
            conn.commit()
            conn.execute(f"""
                DELETE FROM instrucciones_criticas
                WHERE id NOT IN (
                    SELECT id FROM instrucciones_criticas
                    ORDER BY id DESC
                    LIMIT {MAX_INSTRUCCIONES_CRITICAS}
                )
            """)
            conn.commit()

def guardar(role: str, content: str):
    """
    Guarda mensaje en la tabla mensajes (sanitizado)
    y, si es de usuario, extrae instrucciones críticas.
    """
    limpio = _sanear_contenido(role, content)

    with lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO mensajes (role, content) VALUES (?, ?)",
                (role, limpio)
            )
            conn.commit()
            conn.execute(f"""
                DELETE FROM mensajes
                WHERE id NOT IN (
                    SELECT id FROM mensajes
                    ORDER BY id DESC
                    LIMIT {MAX_MENSAJES}
                )
            """)
            conn.commit()

    if role == "user":
        criticas = _extraer_instrucciones_criticas(content)
        _guardar_instrucciones_criticas(criticas)

def historial() -> List[Dict[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM mensajes ORDER BY id ASC"
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

def obtener_instrucciones_criticas() -> str:
    """
    Devuelve un bloque de texto con las instrucciones críticas acumuladas.
    Esto se inyecta como mensaje de sistema adicional.
    """
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT content FROM instrucciones_criticas ORDER BY id ASC"
        ).fetchall()

    if not rows:
        return ""

    lineas = [f"- {r[0]}" for r in rows if r[0].strip()]
    if not lineas:
        return ""

    return (
        "INSTRUCCIONES CRÍTICAS DEL USUARIO (MEMORIA PERSISTENTE):\n"
        "Estas son instrucciones importantes que debes respetar en este proyecto:\n\n"
        + "\n".join(lineas)
    )

# ==========================================================
# ELECCIÓN DE MODELO (TEXTO)
# ==========================================================
def elegir_modelo_texto(mensaje: str) -> str:
    """
    Router simple de modelos. Puedes ampliarlo si quieres usar más modelos.
    Por ahora:
    - Llama 3 70B para casi todo.
    - (Opcional) podrías cambiar a un modelo coder para cosas muy de código.
    """
    m = (mensaje or "").lower()

    # Palabras muy de HTML/CSS/diseño
    palabras_web = [
        "html", "css", "style.css", "frontend", "landing",
        "dashboard", "interfaz", "responsive", "maquetación", "maquetacion",
        "web bonita", "web moderna", "web futurista"
    ]
    if any(p in m for p in palabras_web):
        return "meta-llama/llama-3-70b-instruct"

    # Palabras muy de código duro (podrías rutear a un modelo coder si quieres)
    palabras_codigo = [
        "traceback", "error", "stack", "exception",
        "python", "discord.py", "node", "javascript", "js", "async", "await"
    ]
    if any(p in m for p in palabras_codigo):
        # Podrías usar un modelo tipo coder aquí, pero Llama 3 70B ya va muy bien.
        return "meta-llama/llama-3-70b-instruct"

    # Por defecto
    return "meta-llama/llama-3-70b-instruct"

# ==========================================================
# CONSTRUCCIÓN DE MENSAJES PARA LA API
# ==========================================================
def construir_mensajes(mensaje_usuario: str) -> List[Dict]:
    """
    Construye la lista de mensajes para enviar a OpenRouter:
    - system: INSTRUCCIONES base
    - system: instrucciones críticas (memoria persistente)
    - historial: mensajes previos
    - user: mensaje actual
    """
    mensajes: List[Dict] = []

    # Instrucciones base
    mensajes.append({"role": "system", "content": INSTRUCCIONES})

    # Instrucciones críticas (si las hay)
    criticas = obtener_instrucciones_criticas()
    if criticas:
        mensajes.append({"role": "system", "content": criticas})

    # Historial
    mensajes.extend(historial())

    # Mensaje actual
    mensajes.append({"role": "user", "content": mensaje_usuario})

    return mensajes

# ==========================================================
# STREAMING PARA TEXTO (LLAMA 3 70B)
# ==========================================================
def responder_stream(mensaje: str) -> Generator[str, None, None]:
    """
    Respuesta en streaming usando OpenRouter.
    """
    guardar("user", mensaje)

    url = "https://openrouter.ai/api/v1/chat/completions"
    modelo = elegir_modelo_texto(mensaje)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://lildrakk.github.io",
        "X-Title": "Code IA"
    }

    data = {
        "model": modelo,
        "stream": True,
        "messages": construir_mensajes(mensaje)
    }

    respuesta_completa = ""

    with requests.post(url, json=data, headers=headers, stream=True) as r:
        for linea in r.iter_lines():
            if not linea:
                continue

            try:
                linea = linea.decode("utf-8")

                if not linea.startswith("data: "):
                    continue

                contenido = linea[6:]

                if contenido == "[DONE]":
                    break

                j = json.loads(contenido)
                delta = j["choices"][0]["delta"].get("content", "")

                if delta:
                    respuesta_completa += delta
                    yield delta

            except Exception as e:
                print("ERROR STREAM:", e)

    guardar("assistant", respuesta_completa)

# ==========================================================
# RESPUESTA SIN STREAM (POR SI LA NECESITAS)
# ==========================================================
def responder_texto_simple(mensaje: str) -> str:
    """
    Versión no streaming, por si en algún momento la quieres usar.
    """
    guardar("user", mensaje)

    url = "https://openrouter.ai/api/v1/chat/completions"
    modelo = elegir_modelo_texto(mensaje)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://lildrakk.github.io",
        "X-Title": "Code IA"
    }

    data = {
        "model": modelo,
        "messages": construir_mensajes(mensaje)
    }

    r = requests.post(url, json=data, headers=headers)
    j = r.json()
    respuesta = j["choices"][0]["message"]["content"]

    guardar("assistant", respuesta)
    return respuesta

# ==========================================================
# VISIÓN (LLaVA) — SOLO IMÁGENES
# ==========================================================
def responder_imagen(imagenes_b64: List[str]) -> str:
    """
    Analiza solo imágenes (capturas de código, errores, diseños, etc.).
    """
    guardar("user", "[IMAGEN]")

    url = "https://openrouter.ai/api/v1/chat/completions"

    mensajes = [
        {"role": "system", "content": INSTRUCCIONES},
        *historial(),
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analiza estas imágenes y extrae todo el código, errores o información útil. "
                        "Si hay HTML/CSS/JS, arréglalo y devuélvelo limpio, moderno y profesional. "
                        "Si hay código Python, Discord.py o JavaScript, también arréglalo y explícalo."
                    )
                },
                *[
                    {"type": "image_url", "image_url": f"data:image/png;base64,{img}"}
                    for img in imagenes_b64
                ]
            ]
        }
    ]

    data = {
        "model": "llava-hf/llava-1.5-7b-hf",
        "messages": mensajes
    }

    r = requests.post(url, json=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    })

    j = r.json()
    respuesta = j["choices"][0]["message"]["content"]
    guardar("assistant", respuesta)
    return respuesta

# ==========================================================
# TEXTO + IMÁGENES (LLaVA)
# ==========================================================
def responder_mixto(mensaje: str, imagenes_b64: List[str]) -> str:
    """
    Combina texto del usuario + imágenes (por ejemplo, captura de un error + explicación).
    """
    guardar("user", mensaje + " [IMAGEN]")

    url = "https://openrouter.ai/api/v1/chat/completions"

    mensajes = [
        {"role": "system", "content": INSTRUCCIONES},
        *historial(),
        {
            "role": "user",
            "content": [
                {"type": "text", "text": mensaje},
                *[
                    {"type": "image_url", "image_url": f"data:image/png;base64,{img}"}
                    for img in imagenes_b64
                ]
            ]
        }
    ]

    data = {
        "model": "llava-hf/llava-1.5-7b-hf",
        "messages": mensajes
    }

    r = requests.post(url, json=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    })

    j = r.json()
    respuesta = j["choices"][0]["message"]["content"]
    guardar("assistant", respuesta)
    return respuesta
