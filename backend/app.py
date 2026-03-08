from flask import Flask, request, Response
from flask_cors import CORS
from ia import responder_stream, responder_imagen, responder_mixto
import os
import base64

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return "Servidor activo"

@app.post("/api/chat")
def chat():
    """
    Ruta multimodal:
    - Si solo hay texto → streaming
    - Si solo hay imágenes → análisis de imágenes
    - Si hay texto + imágenes → análisis mixto
    """

    # Si viene como multipart/form-data (con imágenes)
    if request.content_type.startswith("multipart/form-data"):
        mensaje = request.form.get("mensaje", "").strip()
        imagenes = request.files.getlist("imagenes")

        # Convertir imágenes a base64
        imagenes_b64 = []
        for img in imagenes:
            ext = img.filename.lower()
            if not ext.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                continue

            imagenes_b64.append(base64.b64encode(img.read()).decode("utf-8"))

        # Caso 1: solo imágenes
        if not mensaje and imagenes_b64:
            respuesta = responder_imagen(imagenes_b64)
            return Response(respuesta, mimetype="text/plain")

        # Caso 2: texto + imágenes
        if mensaje and imagenes_b64:
            respuesta = responder_mixto(mensaje, imagenes_b64)
            return Response(respuesta, mimetype="text/plain")

        # Caso 3: solo texto (pero enviado como form-data)
        if mensaje and not imagenes_b64:
            return Response(responder_stream(mensaje), mimetype="text/plain")

    # Si viene como JSON (solo texto)
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return Response("No recibí ningún mensaje.", mimetype="text/plain")

    # Streaming normal
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
