from flask import Flask, request, Response
from flask_cors import CORS
from ia import responder_stream
import os

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return "Servidor activo"

# STREAMING REAL
@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return Response("No recibí ningún mensaje.", mimetype="text/plain")

    def generar():
        try:
            for chunk in responder_stream(mensaje):
                yield chunk
        except GeneratorExit:
            print("Cliente canceló la conexión.")
        except Exception as e:
            print("ERROR STREAM:", e)
            yield "⚠️ Error procesando la respuesta."

    return Response(generar(), mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
