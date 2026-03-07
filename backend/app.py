from flask import Flask, request, jsonify
from ia import responder

app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("mensaje", "")
    respuesta = responder(mensaje)
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True)
