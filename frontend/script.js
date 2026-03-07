async function enviar() {
    const input = document.getElementById("mensaje");
    const texto = input.value.trim();

    if (texto === "") return;

    // Mostrar mensaje del usuario
    agregarMensaje("usuario", texto);

    input.value = "";

    try {
        const respuesta = await fetch("http://localhost:5000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mensaje: texto })
        });

        const data = await respuesta.json();

        // Mostrar respuesta de la IA
        agregarMensaje("ia", data.respuesta);

    } catch (error) {
        agregarMensaje("ia", "⚠️ Error al conectar con el servidor.");
    }
}

function agregarMensaje(tipo, texto) {
    const chat = document.getElementById("chat");

    const div = document.createElement("div");
    div.className = tipo === "usuario" ? "mensaje-usuario" : "mensaje-ia";
    div.textContent = texto;

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}
