from flask import Flask, request, jsonify
from flask_cors import CORS
from ia import responder
import os

app = Flask(__name__)
CORS(app)

# Ruta GET para que Render no devuelva 405
@app.get("/")
def home():
    return "Servidor activo"

# Ruta POST para tu IA
@app.post("/api/chat")
def chat():
    # Leer JSON del frontend
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "").strip()

    # Si viene vacío, avisar
    if not mensaje:
        return jsonify({"respuesta": "No recibí ningún mensaje."})

    try:
        # Llamada a tu IA DeepSeek
        respuesta = responder(mensaje)

        if not respuesta:
            respuesta = "No pude generar una respuesta."

    except Exception as e:
        print("ERROR EN responder():", e)
        respuesta = "Hubo un error procesando tu mensaje."

    return jsonify({"respuesta": respuesta})

# Iniciar servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
