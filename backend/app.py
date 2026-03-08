from flask import Flask, request, jsonify
from flask_cors import CORS
from ia import responder
import os

app = Flask(__name__)
CORS(app)  # Permite que tu frontend llame al backend

# Ruta GET para que Render no devuelva 405
@app.get("/")
def home():
    return "Servidor activo"

# Ruta POST para tu IA
@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "")

    # Evitar errores si llega vacío
    if not mensaje:
        return jsonify({"respuesta": "No recibí ningún mensaje."})

    respuesta = responder(mensaje)
    return jsonify({"respuesta": respuesta})

# Iniciar servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
