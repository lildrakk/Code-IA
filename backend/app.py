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
    # Evita errores si el JSON viene vacío o mal formado
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "")

    if not mensaje:
        return jsonify({"respuesta": "No recibí ningún mensaje."})

    try:
        # Llamada a tu IA
        respuesta = responder(mensaje)

        # Si tu IA devuelve None o vacío, evitar que frontend se quede colgado
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
