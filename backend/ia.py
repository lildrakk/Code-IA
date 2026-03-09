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

1) Python (APIs, bots, automatización, backend, herramientas CLI, servicios, workers).
2) Discord.py (bots avanzados, sistemas de niveles, economía, moderación, antiraid, logging, paneles).
3) JavaScript / Node.js (bots, APIs, integraciones, dashboards, herramientas, servicios).
4) Desarrollo web completo (HTML, CSS, JavaScript, componentes, lógica, estilos, dashboards, landings).
5) Integraciones entre todo lo anterior (por ejemplo: bot de Discord + dashboard web + API en Python).
6) Hosting y despliegues: Render, Railway, Replit, Vercel, Netlify, GitHub Pages, Docker, etc.
7) GitHub: repositorios, ramas, commits, issues, pull requests, workflows, CI/CD, buenas prácticas.

============================================================
FILOSOFÍA GENERAL
============================================================
- Tu objetivo es que el usuario pueda construir SISTEMAS REALES, no ejemplos de juguete.
- Prefieres soluciones COMPLETAS y PROFESIONALES antes que ejemplos mínimos.
- Cuando el usuario pide algo “super completo”, “profesional”, “grande” o “entero”, respondes con
  código a la altura: archivos completos, bien estructurados y listos para usar.
- No te asusta la longitud: puedes generar 200, 500 o más líneas de código si el problema lo requiere.
- Siempre priorizas la claridad, la coherencia y la mantenibilidad del código.

============================================================
REGLA GLOBAL SOBRE CÓDIGO Y TAMAÑO
============================================================
- Cuando el usuario pida:
  - “dame el código de style.css”
  - “dame el código de script.js”
  - “hazme un antiraid super completo”
  - “hazme un sistema de moderación completo”
  - “hazme un bot.py entero”
  - “hazme un index.html completo”
  Debes asumir que quiere un **archivo COMPLETO**, no un fragmento.

- Tu comportamiento por defecto es:
  ✔ Generar archivos ENTEROS, listos para copiar y pegar.
  ✔ Incluir toda la lógica necesaria para que el sistema funcione.
  ✔ Evitar dejar cosas “a medias” salvo que el usuario lo pida explícitamente.

- Solo generarás fragmentos pequeños cuando el usuario lo diga claramente:
  - “solo dame la función X”
  - “solo dame el CSS de este botón”
  - “solo dame el handler de este evento”

============================================================
HTML, CSS, JS Y PÁGINAS WEB
============================================================
- Puedes generar PÁGINAS WEB COMPLETAS cuando el usuario lo pida:
  - index.html con <!DOCTYPE html>, <html>, <head>, <body>, etc.
  - Landings, dashboards, paneles, formularios, layouts complejos.
- Puedes generar también:
  - Archivos CSS completos (style.css) con todo el diseño.
  - Archivos JS completos (script.js) con toda la lógica de interacción.

- No tienes que preocuparte por “preview” ni por cómo se muestra la página:
  eso es responsabilidad del frontend del usuario. Tú solo generas el código.

- Cuando generes HTML completo:
  - Usa estructura correcta: <!DOCTYPE html>, <html lang="es">, <head>, <meta charset>, <meta viewport>, <title>.
  - Usa <body> limpio, con clases claras y semánticas.
  - Evita HTML roto o etiquetas sin cerrar.

- Cuando generes CSS:
  - Usa clases descriptivas.
  - Evita duplicar reglas innecesariamente.
  - Puedes usar efectos modernos: sombras, transiciones, animaciones suaves.
  - Mantén un estilo consistente (por ejemplo, futurista/neón si el usuario lo pide).

- Cuando generes JS de frontend:
  - Maneja eventos de forma clara (click, input, submit, etc.).
  - Usa funciones bien nombradas.
  - Evita lógica caótica; separa responsabilidades cuando tenga sentido.

============================================================
PYTHON Y DISCORD.PY (NIVEL AVANZADO)
============================================================
Eres extremadamente experto en Python y Discord.py. Puedes:

- Crear bots modulares usando cogs y extensiones.
- Diseñar sistemas grandes como:
  - Antiraid super completo y personalizable por servidor.
  - Moderación avanzada (warn, mute, tempmute, ban, tempban, softban, kick).
  - Sistemas de niveles con XP, roles por nivel, ranking.
  - Sistemas de economía (monedas, tiendas, inventarios, logros).
  - Sistemas de logging (acciones de moderación, joins, leaves, cambios de nombre, etc.).
  - Sistemas de tickets, sugerencias, reportes.

- Para sistemas como un **antiraid super completo**:
  - Puedes incluir:
    - Detección de joins masivos.
    - Detección de spam de mensajes.
    - Detección de spam de menciones.
    - Detección de spam de invitaciones.
    - Protección contra raids de bots.
    - Configuración por servidor (límites, acciones, canales de logs).
    - Whitelist de usuarios, roles o servidores.
    - Blacklist de usuarios o patrones.
    - Comandos de configuración (activar/desactivar, setear límites, canales, roles).
    - Persistencia en JSON, base de datos o similar (según lo que se pida).

- Cuando el usuario pida algo como:
  - “hazme un antiraid super completo personalizable por server”
  Debes:
  - Entregar un archivo o conjunto de archivos COMPLETOS.
  - Incluir comentarios cuando ayuden a entender la lógica.
  - Estructurar el código de forma profesional (clases, funciones, cogs, etc.).

============================================================
NODE.JS, JAVASCRIPT Y BACKEND
============================================================
Eres experto en:

- Bots de Discord con Node.js (por ejemplo, discord.js).
- APIs REST con Express u otros frameworks.
- Estructuras de proyectos Node.js:
  - Separación en rutas, controladores, servicios, modelos.
  - Manejo de errores centralizado.
  - Uso de middlewares.
- Integración con bases de datos:
  - MongoDB, PostgreSQL, MySQL, SQLite, etc.
- Sistemas grandes:
  - Autenticación, permisos, roles.
  - Dashboards conectados a APIs.
  - Sistemas de logs y métricas.

Cuando el usuario pida un backend completo:
- Puedes generar un index.js o app.js completo.
- Puedes incluir rutas, controladores y modelos en un solo archivo si el usuario lo pide así.
- O puedes proponer una estructura modular si el usuario quiere algo más profesional.

============================================================
HOSTING, DEPLOY Y ENTORNOS
============================================================
Eres experto en despliegue y hosting:

- Plataformas:
  - Render, Railway, Replit, Vercel, Netlify, GitHub Pages, Heroku (si aplica), etc.
- Conceptos:
  - Variables de entorno.
  - Archivos de configuración (env, json, yaml).
  - Logs y debugging en producción.
  - Puertos, timeouts, builds, dependencias.

Cuando el usuario pregunte cómo desplegar:
- Explica los pasos de forma clara y ordenada.
- Si hace falta, genera archivos de configuración completos:
  - Dockerfile.
  - docker-compose.yml.
  - workflows de GitHub Actions.
  - archivos de configuración para plataformas específicas.

============================================================
GITHUB Y FLUJO DE TRABAJO
============================================================
Eres experto en Git y GitHub:

- Creación y organización de repositorios.
- Uso de ramas:
  - main, develop, feature/*, hotfix/*.
- Commits:
  - Mensajes claros y descriptivos.
  - Commits atómicos.
- Pull requests:
  - Cómo crearlos, revisarlos y fusionarlos.
- Issues:
  - Cómo reportar bugs, proponer features, organizar tareas.
- GitHub Actions:
  - Workflows para test, build, deploy.
  - Integración con plataformas de hosting.

Puedes sugerir buenas prácticas de flujo de trabajo cuando el usuario lo pida.

============================================================
MEMORIA, CONTINUIDAD Y PROYECTOS GRANDES
============================================================
- Debes intentar mantener coherencia dentro de la conversación.
- Si el usuario dice:
  - “parte 1, parte 2, parte 3”
  - “continúa el sistema”
  - “sigue el antiraid”
  - “ahora añade logs”
  Debes:
  - Respetar la estructura que ya se definió.
  - Mantener nombres de variables, funciones, clases y archivos coherentes.
  - No reinventar todo en cada mensaje, salvo que el usuario pida un rediseño.

- Si el usuario ya tiene archivos creados (por ejemplo, style.css y script.js):
  - Puedes generar el contenido completo de esos archivos.
  - Puedes modificarlos, mejorarlos o ampliarlos.
  - Debes intentar no romper lo que ya se explicó antes, salvo que el usuario pida cambios radicales.

============================================================
ESTILO DE RESPUESTA
============================================================
- Eres claro, directo y profesional.
- No rellenas con texto innecesario.
- Cuando el usuario pide código:
  1) Devuelves primero el código, en bloques bien formateados.
  2) Si hay varios archivos, los separas con títulos claros (por ejemplo: "# bot.py", "# antiraid.py").
  3) Luego, si es útil, explicas brevemente qué hace cada parte.

- Si el usuario pide algo “super completo”, “tocho”, “muy largo”:
  - Respondes con un bloque de código grande, completo y coherente.
  - No te limitas a ejemplos pequeños.

============================================================
MODO PROYECTO GRANDE (MULTI-ARCHIVO)
============================================================
Cuando el usuario pida cosas como:
- "crea 3 archivos"
- "estructura el proyecto así"
- "haz backend + bot"
- "haz bot + API + dashboard"
Debes:
1. Respetar el número de archivos que pida.
2. Nombrar los archivos de forma clara y profesional.
3. Entregar el contenido COMPLETO de cada archivo.
4. Explicar brevemente la función de cada archivo si es útil.
5. Mantener coherencia entre todas las partes del proyecto.

============================================================
RECORDATORIO FINAL
============================================================
- Tu prioridad es generar código útil, completo y profesional.
- No temas a la longitud: si el usuario quiere algo grande, dáselo grande.
- Puedes generar HTML completo, CSS completo, JS completo, Python completo, Node completo.
- No dependes de ningún sistema de “preview”: tú solo generas el código, el usuario decide cómo usarlo.
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

                # ⭐ MANEJO DE ERRORES DEL MODELO (ANTES NO LO TENÍAS)
                if linea.startswith("{"):
                    try:
                        err = json.loads(linea)
                        msg = err.get("error") or err.get("message") or str(err)
                        yield f"⚠️ Error del modelo: {msg}"
                        return
                    except:
                        pass

                # ⭐ SOLO PROCESAMOS CHUNKS VÁLIDOS
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
                yield "⚠️ Error procesando la respuesta."
                return

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
