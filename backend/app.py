from flask import Flask, request, jsonify
from flask_cors import CORS
from ia import responder
import os

app = Flask(__name__)
CORS(app)  # ← Permite que tu frontend llame al backend

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("mensaje", "")
    respuesta = responder(mensaje)
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
